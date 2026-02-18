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

resource_path = 'resources/twitter_tl_xapi'
from . import xm
from utils.tz import beijingnow, SHA_TZ
from utils import fileio

lock = asyncio.Lock()
crontab = croniter('*/2 * * * *', beijingnow())
crontab_next = crontab.get_next(datetime)

# X API v2 频率控制：
# - 免费层级：每月 1500 次推文查询
# - 建议间隔：每个用户检查间隔 10 秒
# - 每次检查调用：get_user_by_username + get_user_tweets
# - 错误恢复：60 秒间隔防止速率限制

async def timeline_withxapi():
    global lock, crontab, crontab_next, resource_path
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                subscribes = await fileio.read_json(join(resource_path, 'subscribes.json'))
                for username in subscribes:
                    try:
                        data = await fileio.read_json(join(resource_path, 'data.json'))
                        # 初始化用户数据
                        if username not in data:
                            # 获取用户信息
                            resp = xm.get_user_by_username(username)
                            if resp.status_code != 200:
                                logger.error(f"Failed to get user info for {username}: {resp.status_code}")
                                continue
                            
                            user_info_json = resp.json()
                            user_info = xm.parse_user(user_info_json)
                            
                            if not user_info:
                                logger.error(f"Failed to parse user info for username: {username}")
                                continue
                            
                            data[username] = copy.deepcopy(user_info)
                            
                            # 获取时间线
                            tl_resp = xm.get_user_tweets(user_info['id'], max_results=10)
                            if tl_resp.status_code != 200:
                                logger.error(f"Failed to get timeline for {username}: {tl_resp.status_code}")
                                continue
                            
                            timeline_json = tl_resp.json()
                            timeline_result = xm.parse_tweets(timeline_json)
                            
                            if not timeline_result:
                                logger.warning(f"No tweets found for {username}")
                                data[username]['timeline'] = {}
                            else:
                                # 转换为字典格式，以推文ID为键
                                timeline = {tweet['id']: tweet for tweet in timeline_result['tweets']}
                                data[username]['timeline'] = timeline
                            
                            await fileio.write_json(join(resource_path, "data.json"), data)
                        
                        # 检查更新
                        else:
                            # 更新用户信息
                            resp = xm.get_user_by_username(username)
                            if resp.status_code != 200:
                                logger.error(f"Failed to get user info for {username}: {resp.status_code}")
                                continue
                            
                            user_info_json = resp.json()
                            user_info = xm.parse_user(user_info_json)
                            
                            if user_info is None:
                                logger.error(f"Failed to parse user info for username: {username}. API response might be invalid or user does not exist.")
                                continue

                            for k, v in user_info.items():
                                # 会反复横跳抽风，就不要了
                                if k == 'following_count':
                                    continue
                                if v != data[username][k]:
                                    for group in subscribes[username]['groups']:
                                        if k == 'icon':
                                            t = f"{data[username]['name']}更新了{k}\n"
                                            try:
                                                await action.sendGroupPic(group=group, text=t, url=v)
                                            except Exception:
                                                logger.exception(f'sendGroupPic failed group={group} k={k}')
                                        elif k == 'followers_count':
                                            if int(v/1000) > int(data[username][k]/1000):
                                                t = f"{data[username]['name']}粉丝数到达{v}"
                                                try:
                                                    await action.sendGroupText(group=group, text=t)
                                                except Exception:
                                                    logger.exception(f'sendGroupText failed group={group} k={k}')
                                        else:
                                            t = f"{data[username]['name']}更新了{k}\n从\n{data[username][k]}\n更改为\n{v}"
                                            try:
                                                await action.sendGroupText(group=group, text=t)
                                            except Exception:
                                                logger.exception(f'sendGroupText failed group={group} k={k}')
                                    data[username][k] = v
                                    await fileio.write_json(join(resource_path, "data.json"), data)
                            
                            # 获取时间线
                            tl_resp = xm.get_user_tweets(user_info['id'], max_results=10)
                            if tl_resp.status_code != 200:
                                logger.error(f"Failed to get timeline for {username}: {tl_resp.status_code}")
                                continue
                            
                            timeline_json = tl_resp.json()
                            timeline_result = xm.parse_tweets(timeline_json)
                            
                            if not timeline_result:
                                logger.warning(f"No tweets in timeline for {username}")
                                continue
                            
                            # 转换为字典格式
                            timeline = {tweet['id']: tweet for tweet in timeline_result['tweets']}
                            
                            new_tweets = [tid for tid in timeline if tid not in data[username]['timeline']]
                            
                            for tweet_id in new_tweets:
                                tdata = timeline[tweet_id]
                                url = f'https://twitter.com/{username}/status/{tdata["id"]}'
                                created_at = parser.parse(tdata['created_at']).astimezone(SHA_TZ)
                                
                                # 超过10分钟的推默认超时, 不再处理
                                now = datetime.now(SHA_TZ)
                                if now - created_at > timedelta(minutes=10):
                                    continue
                                
                                imgs = None
                                videos = None
                                
                                # 判断推文类型
                                referenced_tweets = tdata.get('referenced_tweets', [])
                                
                                if not referenced_tweets:
                                    # 普通推文
                                    t = f"{user_info['name']}的新推\n发布于{created_at}\n\n{tdata['text']}\n\n{url}"
                                    imgs = tdata.get('imgs')
                                    videos = tdata.get('videos')
                                
                                elif referenced_tweets[0]['type'] == 'retweeted':
                                    # 转推
                                    # 注意：X API v2 不提供被转推内容的详细信息
                                    # 我们只显示转推的事实
                                    t = f"{user_info['name']}转推了\n发布于{created_at}\n\n{tdata['text']}\n\n{url}"
                                    imgs = tdata.get('imgs')
                                    videos = tdata.get('videos')
                                
                                elif referenced_tweets[0]['type'] == 'quoted':
                                    # 引用推文
                                    t = f"{user_info['name']}引用转推\n发布于{created_at}\n\n{tdata['text']}\n\n{url}"
                                    imgs = tdata.get('imgs')
                                    videos = tdata.get('videos')
                                
                                else:
                                    # 其他类型（如回复）
                                    t = f"{user_info['name']}的新推\n发布于{created_at}\n\n{tdata['text']}\n\n{url}"
                                    imgs = tdata.get('imgs')
                                    videos = tdata.get('videos')
                                
                                for group in subscribes[username]['groups']:
                                    if imgs:
                                        try:
                                            await action.sendGroupPic(group=group, text=t, url=imgs)
                                        except Exception:
                                            logger.exception(f'sendGroupPic failed group={group}')
                                    elif videos:
                                        # TODO: 暂无上传视频的接口
                                        pass
                                    else:
                                        try:
                                            await action.sendGroupText(group=group, text=t)
                                        except Exception:
                                            logger.exception(f'sendGroupText failed group={group}')
                                
                                data[username]['timeline'][tweet_id] = timeline[tweet_id]
                                await fileio.write_json(join(resource_path, 'data.json'), data)
                            
                            # sync timeline for deleted tweets
                            deleted_tweets = [tid for tid in data[username]['timeline'] if tid not in timeline]
                            if deleted_tweets:
                                for tid in deleted_tweets:
                                    del data[username]['timeline'][tid]
                                await fileio.write_json(join(resource_path, 'data.json'), data)
                        
                        await asyncio.sleep(10)
                    
                    except Exception as e:
                        logger.exception(f'twitter tl (xapi) scheduler error username: {username}')
                        t = f'twitter tl (xapi) scheduler error\nusername: {username}\ntraceback: {traceback.format_exc()}'
                        # text过长可能发送失败，改为简单提示
                        try: 
                            await action.sendGroupText(group=1014696092, text=t)
                        except:
                            await action.sendGroupText(group=1014696092, text=f'twitter tl (xapi) scheduler error\nusername: {username}')
                        await asyncio.sleep(300)
                        
                data = await fileio.read_json(join(resource_path, "data.json"))
                username_to_del = []
                for username in data:
                    if username not in subscribes:
                        username_to_del.append(username)
                for username in username_to_del:
                    del data[username]
                await fileio.write_json(join(resource_path, "data.json"), data)
                
                crontab_next = crontab.get_next(datetime)
