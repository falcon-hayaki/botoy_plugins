import asyncio
import copy
import traceback
from os.path import join
from croniter import croniter
from datetime import datetime, timedelta
from dateutil import parser
from botoy import ctx, action, jconfig
import logging

logger = logging.getLogger(__name__)

resource_path = 'resources/twitter_tl'
from . import tm
from utils.tz import beijingnow, SHA_TZ
from utils import fileio

lock = asyncio.Lock()
crontab = croniter('*/5 * * * *', beijingnow())
crontab_next = crontab.get_next(datetime)

async def timeline():
    global lock, crontab, crontab_next, resource_path
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                subscribes = await fileio.read_json(join(resource_path, 'subscribes.json'))
                for uid in subscribes:
                    try:
                        data = await fileio.read_json(join(resource_path, 'data.json'))
                        # 初始化用户数据
                        if uid not in data:
                            # 获取用户信息并安全解析 JSON，失败时记录响应内容以便排查
                            resp = tm.get_user_info(uid)
                            try:
                                user_info_json = resp.json()
                            except Exception:
                                logger.error("get_user_info json decode failed, uid=%s status=%s text=%s", uid, getattr(resp, 'status_code', None), getattr(resp, 'text', repr(resp)))
                                raise
                            user_info = tm.parse_user_info(user_info_json)
                            data[uid] = copy.deepcopy(user_info)
                            # 获取时间线并安全解析 JSON，失败时记录响应内容以便排查
                            tl_resp = tm.get_user_timeline(data[uid]['id'])
                            try:
                                timeline_row = tl_resp.json()
                            except Exception:
                                logger.error("get_user_timeline json decode failed, uid=%s status=%s text=%s", uid, getattr(tl_resp, 'status_code', None), getattr(tl_resp, 'text', repr(tl_resp)))
                                raise ValueError(f'tl value error: status={getattr(tl_resp, "status_code", None)}')
                            timeline = tm.parse_timeline(timeline_row)
                            if timeline is None:
                                raise ValueError(f'tl value error: {timeline_row}')
                            # handle errors
                            elif 'errors' in timeline:
                                return
                            data[uid]['timeline'] = timeline
                        # 检查更新
                        else:
                            # 更新用户信息，使用安全的 JSON 解析并在失败时记录响应
                            resp = tm.get_user_info(uid)
                            try:
                                user_info_json = resp.json()
                            except Exception:
                                logger.error("get_user_info json decode failed (update), uid=%s status=%s text=%s", uid, getattr(resp, 'status_code', None), getattr(resp, 'text', repr(resp)))
                                raise
                            user_info = tm.parse_user_info(user_info_json)
                            for k, v in user_info.items():
                                # 会反复横跳抽风，就不要了
                                if k == 'following_count':
                                    continue
                                if v != data[uid][k]:
                                    for group in subscribes[uid]['groups']:
                                        if k == 'icon':
                                            t = f"{data[uid]['name']}更新了{k}\n"
                                            await action.sendGroupPic(group=group, text=t, url=v)
                                        elif k == 'followers_count':
                                            if int(v/1000) > int(data[uid][k]/1000):
                                                t = f"{data[uid]['name']}粉丝数到达{v}"
                                                await action.sendGroupText(group=group, text=t)
                                        else:
                                            t = f"{data[uid]['name']}更新了{k}\n从\n{data[uid][k]}\n更改为\n{v}"
                                            await action.sendGroupText(group=group, text=t)
                                    data[uid][k] = v
                            tl_resp = tm.get_user_timeline(data[uid]['id'])
                            try:
                                timeline_json = tl_resp.json()
                            except Exception:
                                logger.error("get_user_timeline json decode failed (update), uid=%s status=%s text=%s", uid, getattr(tl_resp, 'status_code', None), getattr(tl_resp, 'text', repr(tl_resp)))
                                raise ValueError(f'tl value error: status={getattr(tl_resp, "status_code", None)}')
                            timeline = tm.parse_timeline(timeline_json)
                            if timeline is None:
                                raise ValueError(f'tl value error: {timeline_row}')
                            # handle errors
                            elif 'errors' in timeline:
                                return
                            new_tweets = [t for t in timeline if t not in data[uid]['timeline']]
                            for t in new_tweets:
                                tdata = timeline[t]
                                url = f'https://twitter.com/{uid}/status/{tdata["id"]}'
                                tweet_type = tdata['tweet_type']
                                created_at = parser.parse(tdata['created_at']).astimezone(SHA_TZ)
                                # 超过10分钟的推默认超时, 不再处理
                                now = datetime.now(SHA_TZ)
                                imgs = None
                                videos = None
                                if now - created_at > timedelta(minutes=10):
                                    continue
                                if tweet_type == 'default':
                                    t = f"{user_info['name']}的新推\n发布于{created_at}\n\n{tdata['text']}\n\n{url}"
                                    imgs = tdata.get('imgs')
                                    videos = tdata.get('videos')
                                elif tweet_type == 'retweet':
                                    retweet_data = tdata['retweet_data']
                                    origin_created_at = parser.parse(retweet_data['data']['created_at']).astimezone(SHA_TZ)
                                    t = f"{user_info['name']}转推了\n转发自:\n{retweet_data['user_info']['name']}发布于{origin_created_at}\n\n{retweet_data['data']['text']}\n\n{url}"
                                    imgs = retweet_data['data'].get('imgs')
                                    videos = retweet_data['data'].get('videos')
                                elif tweet_type == 'quote':
                                    quote_data = tdata['quote_data']
                                    origin_created_at = parser.parse(quote_data['data']['created_at']).astimezone(SHA_TZ)
                                    t = f"{user_info['name']}转推了\n发布于{created_at}\n\n{tdata['text']}\n\n转发自:\n{quote_data['user_info']['name']}发布于{origin_created_at}\n\n{quote_data['data']['text']}\n\n{url}"
                                    imgs = quote_data['data'].get('imgs')
                                    videos = quote_data['data'].get('videos')
                                for group in subscribes[uid]['groups']:
                                    if imgs:
                                        await action.sendGroupPic(group=group, text=t, url=imgs)
                                    elif videos:
                                        # TODO: 暂无上传视频的接口
                                        pass
                                    else:
                                        await action.sendGroupText(group=group, text=t)
                            data[uid]['timeline'] = copy.deepcopy(timeline)
                        await fileio.write_json(join(resource_path, "data.json"), data)
                        await asyncio.sleep(5)
                    except Exception as e:
                        logger.exception(f'twitter tl scheduler error uid: {uid}')
                        t = f'twitter tl scheduler error\nuid: {uid}\ntraceback: {traceback.format_exc()}'
                        await action.sendGroupText(group=1014696092, text=t)
                        await asyncio.sleep(300)
                        
                data = await fileio.read_json(join(resource_path, "data.json"))
                uid_to_del = []
                for uid in data:
                    if uid not in subscribes:
                        uid_to_del.append(uid)
                for uid in uid_to_del:
                    del data[uid]
                await fileio.write_json(join(resource_path, "data.json"), data)
                
                crontab_next = crontab.get_next(datetime)