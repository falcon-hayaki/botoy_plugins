import asyncio
import copy
import traceback
from os.path import join
from croniter import croniter
from datetime import datetime, timedelta
from dateutil import parser
from botoy import ctx, action, jconfig, S
import logging

logger = logging.getLogger(__name__)

resource_path = 'resources/ytb_live_stream'
from . import ym
from utils.tz import beijingnow, SHA_TZ
from utils import fileio

lock = asyncio.Lock()
crontab = croniter('*/5 * * * *', beijingnow())
crontab_next = crontab.get_next(datetime)

async def ytbtimeline():
    global lock, crontab, crontab_next, resource_path
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                subscribes = await fileio.read_json(join(resource_path, 'subscribes.json'))
                for uid in subscribes:
                    try:
                        data = await fileio.read_json(join(resource_path, 'data.json'))
                        if uid not in data or not isinstance(data[uid], dict):
                            data[uid] = {}
                        # get plaiylsit id
                        now = datetime.now()
                        if 'playlist_id' not in data[uid] or (now - parser.parse(data[uid]['playlist_id_update_at']) > timedelta(days=1)):
                            code, channel_details = ym.get_channel_details(uid, subscribes[uid]['id_type'])
                            if code != 0:
                                raise ValueError(f'get_channel_details error: {uid} {channel_details}')
                            playlist_id = channel_details['contentDetails']['relatedPlaylists']['uploads']
                            data[uid]['playlist_id'] = playlist_id
                            data[uid]['playlist_id_update_at'] = now.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            playlist_id = data[uid]['playlist_id']
                        # get video ids
                        code, video_ids = ym.get_playlist_video_ids(playlist_id)
                        if code != 0:
                            raise ValueError(f'get_playlist_video_ids error: {uid} {video_ids}')
                        # get live stream info
                        code, live_info = ym.check_live_stream(video_ids)
                        if code != 0:
                            raise ValueError(f'check_live_stream error: {uid} {live_info}')
                        
                        messages_to_send = []
                        data_changed = False
                        
                        if 'live_status' in data[uid] and isinstance(data[uid]['live_status'], dict):
                            if not data[uid]['live_status'].get('live', None):
                                data[uid]['live_status']['live'] = {}
                            if not data[uid]['live_status'].get('upcoming', None):
                                data[uid]['live_status']['upcoming'] = {}
                            
                            # new live stream
                            for lid, ldata in live_info['live'].items():
                                if lid not in data[uid]['live_status']['live']:
                                    data[uid]['live_status']['live'][lid] = ldata
                                    data_changed = True
                                    t = f"{ldata['name']}开播了\n"
                                    t += f"标题: {ldata['title']}\n"
                                    actualStartTime = parser.parse(ldata['liveStreamingDetails']['actualStartTime']).astimezone(SHA_TZ)
                                    t += f"开始时间: {actualStartTime.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                                    imgs = ldata['thumbnail']
                                    messages_to_send.append(dict(
                                        type='pic',
                                        text=t,
                                        url=imgs,
                                        groups=subscribes[uid]['groups']
                                    ))
                                if lid in data[uid]['live_status']['upcoming']:
                                    del data[uid]['live_status']['upcoming'][lid]
                                    data_changed = True

                            # new upcoming stream
                            for lid, ldata in live_info['upcoming'].items():
                                if 'scheduledStartTime' not in ldata['liveStreamingDetails']:
                                    continue
                                if lid not in data[uid]['live_status']['upcoming']:
                                    scheduledStartTime = parser.parse(ldata['liveStreamingDetails']['scheduledStartTime']).astimezone(SHA_TZ)
                                    # 使用带时区的时间进行比较
                                    now_with_tz = datetime.now(SHA_TZ)
                                    if scheduledStartTime < now_with_tz:
                                        continue
                                    data[uid]['live_status']['upcoming'][lid] = ldata
                                    data_changed = True
                                    t = f"{ldata['name']}设置了一个直播预约\n"
                                    t += f"标题: {ldata['title']}\n"
                                    t += f"开始时间: {scheduledStartTime.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                                    imgs = ldata['thumbnail']
                                    messages_to_send.append(dict(
                                        type='pic',
                                        text=t,
                                        url=imgs,
                                        groups=subscribes[uid]['groups']
                                    ))
                            
                            # ended stream
                            ldid_to_pop = []
                            for ldid, lddata in data[uid]['live_status']['live'].items():
                                if ldid not in live_info['live']:
                                    ldid_to_pop.append(ldid)
                                    t = f"{lddata['name']}下播了"
                                    messages_to_send.append(dict(
                                        type='text',
                                        text=t,
                                        groups=subscribes[uid]['groups']
                                    ))
                            if ldid_to_pop:
                                data_changed = True
                                for ltp in ldid_to_pop:
                                    data[uid]['live_status']['live'].pop(ltp)
                            
                            # remove upcoming streams that are no longer in the API response
                            # (they may have gone live or been cancelled)
                            ldid_to_pop = []
                            for ldid in data[uid]['live_status']['upcoming'].keys():
                                # 只删除API返回中已经不存在的预约（可能已开播或被取消）
                                if ldid not in live_info['upcoming']:
                                    ldid_to_pop.append(ldid)
                            if ldid_to_pop:
                                data_changed = True
                                for ltp in ldid_to_pop:
                                    data[uid]['live_status']['upcoming'].pop(ltp)
                        else:
                            data[uid]['live_status'] = copy.copy(live_info)
                            data_changed = True
                        
                        if data_changed:
                            await fileio.write_json(join(resource_path, "data.json"), data)
                        
                        for msg in messages_to_send:
                            for group in msg['groups']:
                                if msg['type'] == 'pic':
                                    try:
                                        await action.sendGroupPic(group=group, text=msg['text'], url=msg['url'])
                                    except Exception:
                                        logger.exception(f'sendGroupPic failed group={group}')
                                else:
                                    try:
                                        await action.sendGroupText(group=group, text=msg['text'])
                                    except Exception:
                                        logger.exception(f'sendGroupText failed group={group}')
                        await asyncio.sleep(5)
                    except Exception as e:
                        # 达到api配置限额
                        if 'quota' in traceback.format_exc():
                            crontab_next = [crontab.get_next(datetime) for _ in range(2)][-1]
                            t = f'youtube tl scheduler error\nuid: {uid}\ntraceback: {traceback.format_exc()}'
                            await action.sendGroupText(group=1014696092, text=t)
                            return
                        logger.exception(f'youtube tl scheduler error uid: {uid}')
                        t = f'youtube tl scheduler error\nuid: {uid}\ntraceback: {traceback.format_exc()}'
                        # text过长可能发送失败，改为简单提示
                        try: 
                            await action.sendGroupText(group=1014696092, text=t)
                        except:
                            await action.sendGroupText(group=1014696092, text=f'youtube tl scheduler error\nuid: {uid}')
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
                
async def ytbtimeline_subs():
    if msg := ctx.g:
        if msg.text.strip() in ['ytb订阅', '油管订阅'] and msg.from_user != jconfig.qq:
            subscribes = await fileio.read_json(join(resource_path, 'subscribes.json'))
            uid_list = [u for u, v in subscribes.items() if msg.from_group in v['groups']]
            try:
                t = ''
                for idx, uid in enumerate(uid_list):
                    code, channel_details = ym.get_channel_details(uid, subscribes[uid]['id_type'])
                    if code != 0:
                        raise ValueError(f'get_channel_details error: {uid} {channel_details}')
                    t += f"{channel_details['snippet']['title']}({uid_list[idx]})\n"
                if not t:
                    t = '无'
                t = f"已订阅的频道:\n{t}"
            except Exception as e:
                t = f'发生未知错误'
                await S.text(t)
                t = f'error in get_ytb_video: group={msg.from_group} text={msg.text}\n'
                t += f'traceback: \n {traceback.format_exc()}'
                await action.sendGroupText(group=1014696092, text=t)
            else:
                await S.text(t)
                
async def ytbtimeline_stats():
    if msg := ctx.g:
        if msg.text.strip() in ['ytb状态', '油管状态'] and msg.from_user != jconfig.qq:
            subscribes = await fileio.read_json(join(resource_path, 'subscribes.json'))
            data = await fileio.read_json(join(resource_path, 'data.json'))
            uid_list = [u for u, v in subscribes.items() if msg.from_group in v['groups']]
            if not uid_list:
                await S.text('未订阅任何频道')
            t = '当前ytb状态: \n'
            for uid, v in data.items():
                if uid not in uid_list:
                    continue
                t += f"{uid}:\n"
                if 'live_status' in v and isinstance(v['live_status'], dict):
                    if v['live_status'].get('live', None):
                        for ldata in v['live_status']['live'].values():
                            t += f"正在直播: {ldata['title']}\n"
                    if v['live_status'].get('upcoming', None):
                        for ldata in v['live_status']['upcoming'].values():
                            t += f"直播预约: {ldata['title']}\n"
                            scheduledStartTime = parser.parse(ldata['liveStreamingDetails']['scheduledStartTime']).astimezone(SHA_TZ)
                            t += f"\t开始时间: {scheduledStartTime.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                else:
                    t += '无\n\n'
            await S.text(t)