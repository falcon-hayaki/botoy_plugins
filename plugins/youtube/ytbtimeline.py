import asyncio
import copy
import traceback
from os.path import join
from croniter import croniter
from datetime import datetime, timedelta
from dateutil import parser
from botoy import ctx, action, jconfig

resource_path = 'resources/ytb_live_stream'
from . import ym
from utils.tz import beijingnow, SHA_TZ
from utils import fileio

lock = asyncio.Lock()
crontab = croniter('*/10 * * * *', beijingnow())
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
                        # get real uid
                        if subscribes[uid]['id_type'] == 'handle':
                            code, real_uid = ym.get_channel_id(uid)
                            if code != 0:
                                raise ValueError(f'get_channel_id error: {uid} {real_uid}')
                        else:
                            real_uid = uid
                        # get live stream info
                        code, live_info = ym.check_live_stream(real_uid)
                        if code != 0:
                            raise ValueError(f'check_live_stream error: {uid} {live_info}')
                        
                        if uid in data:
                            if live_info and not data[uid]:
                                t = f"{live_info['name']}开播了\n"
                                t += f"标题: {live_info['title']}\n"
                                t += f"{live_info['description']}\n"
                                # published_at = parser.parse(live_info['publishedAt']).astimezone(SHA_TZ)
                                # t += f"直播时间: {published_at.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                                imgs = live_info['thumbnail']
                                for group in subscribes[uid]['groups']:
                                    await action.sendGroupPic(group=group, text=t, url=imgs)
                            elif not live_info and data[uid]:
                                t = f"{data[uid]['name']}下播了"
                                for group in subscribes[uid]['groups']:
                                    await action.sendGroupText(group=group, text=t)
                                    
                        data[uid] = copy.deepcopy(live_info)
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