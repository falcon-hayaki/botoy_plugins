import asyncio
import copy
import traceback
from os.path import join
from croniter import croniter
from datetime import datetime, timedelta
from dateutil import parser
from botoy import ctx, action, jconfig, S

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
                        
                        if 'live_status' in data[uid]:
                            if live_info['liveBroadcastContent'] != data[uid]['live_status']:
                                if live_info['liveBroadcastContent'] == 'live':
                                    t = f"{live_info['name']}开播了\n"
                                    t += f"标题: {live_info['title']}\n"
                                    # t += f"{live_info['description']}\n"
                                    actualStartTime = parser.parse(live_info['liveStreamingDetails']['actualStartTime']).astimezone(SHA_TZ)
                                    t += f"开始时间: {actualStartTime.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                                    imgs = live_info['thumbnail']
                                    for group in subscribes[uid]['groups']:
                                        await action.sendGroupPic(group=group, text=t, url=imgs)
                                elif live_info['liveBroadcastContent'] == 'upcoming':
                                    t = f"{live_info['name']}设置了一个直播预约\n"
                                    t += f"标题: {live_info['title']}\n"
                                    # t += f"{live_info['description']}\n"
                                    scheduledStartTime = parser.parse(live_info['liveStreamingDetails']['scheduledStartTime']).astimezone(SHA_TZ)
                                    t += f"开始时间: {scheduledStartTime.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                                    imgs = live_info['thumbnail']
                                    for group in subscribes[uid]['groups']:
                                        await action.sendGroupPic(group=group, text=t, url=imgs)
                                elif live_info['liveBroadcastContent'] == 'none':
                                    t = f"{live_info['name']}下播了"
                                    for group in subscribes[uid]['groups']:
                                        await action.sendGroupText(group=group, text=t)
                                else:
                                    t = f'未处理的直播状态: {live_info["liveBroadcastContent"]}\n请联系那个臭写bot的'
                                    for group in subscribes[uid]['groups']:
                                        await action.sendGroupText(group=group, text=t)
                                    
                        data[uid]['live_status'] = live_info['liveBroadcastContent']
                        await fileio.write_json(join(resource_path, "data.json"), data)
                        await asyncio.sleep(5)
                    except Exception as e:
                        # 达到api配置限额
                        if 'quota' in traceback.format_exc():
                            crontab_next = [crontab.get_next(datetime) for _ in range(2)][-1]
                            t = f'youtube tl scheduler error\nuid: {uid}\ntraceback: {traceback.format_exc()}'
                            await action.sendGroupText(group=1014696092, text=t)
                            return
                        print(e, traceback.format_exc())
                        t = f'youtube tl scheduler error\nuid: {uid}\ntraceback: {traceback.format_exc()}'
                        await action.sendGroupText(group=1014696092, text=t)
                        await asyncio.sleep(60)
                        
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