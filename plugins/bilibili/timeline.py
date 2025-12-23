import asyncio
import copy
import re
import traceback
from os.path import join
from croniter import croniter
from datetime import datetime, timedelta
from dateutil import parser
from botoy import ctx, action, jconfig
import logging

logger = logging.getLogger(__name__)

resource_path = 'resources/bili_dynamic'
from . import bm
from utils.tz import beijingnow, SHA_TZ
from utils import fileio

lock = asyncio.Lock()
crontab = croniter('*/5 * * * *', beijingnow())
crontab_next = crontab.get_next(datetime)

async def bili_dynamic_timeline():
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
                            info = bm.get_user_info(uid).json()
                            relation = bm.get_user_relation(uid).json()
                            user_info = bm.parse_user_info(info, relation)
                            data[uid] = copy.deepcopy(user_info)
                            data[uid]['dynamic_id_list'] = []
                            data[uid]['dynamic_data'] = {}
                            await fileio.write_json(join(resource_path, "data.json"), data)
                            timeline_row = bm.get_dynamic_list(uid).json()
                            dynamic_id_list, dynamic_data = bm.parse_timeline(timeline_row)
                            if dynamic_id_list is None:
                                raise ValueError(f'tl value error: {timeline_row}')
                            data[uid]['dynamic_id_list'] = dynamic_id_list
                            data[uid]['dynamic_data'] = dynamic_data
                            await fileio.write_json(join(resource_path, "data.json"), data)
                        # 检查更新
                        else:
                            user_info = bm.parse_user_info(bm.get_user_info(uid).json(), bm.get_user_card(uid).json())
                            for k, v in user_info.items():
                                if v != data[uid][k]:
                                    for group in subscribes[uid]['groups']:
                                        if k in ['face', 'top_photo']:
                                            # NOTE: 同一张图获取到的的cdn地址可能会不同
                                            new_re_res = re.match('.+\/([a-zA-Z0-9]+)\.(?:jpg|png)', v)
                                            old_re_res = re.match('.+\/([a-zA-Z0-9]+)\.(?:jpg|png)', data[uid][k])
                                            if new_re_res and old_re_res and new_re_res.groups()[0] != old_re_res.groups()[0]:
                                                t = f"{data[uid]['name']}更新了{k}:\n{v}"
                                                await action.sendGroupPic(group=group, text=t, url=v)
                                        elif k == 'followers':
                                            if int(v/1000) > int(data[uid][k]/1000):
                                                t = f"{data[uid]['name']}粉丝数到达{v}"
                                                await action.sendGroupText(group=group, text=t)
                                        # 直播间信息
                                        elif k.startswith('live_'):
                                            if k == 'live_status':
                                                if data[uid][k] is not None and data[uid][k] == 1 and v == 0:
                                                    t = f"{data[uid]['name']}下播了\n"
                                                    t += f"本次直播{user_info['live_text']}"
                                                    await action.sendGroupText(group=group, text=t)
                                                elif data[uid][k] is not None and data[uid][k] == 0 and v == 1:
                                                    t = f"{data[uid]['name']}开播了\n"
                                                    t += f"标题：{user_info['live_title']}\n"
                                                    t += user_info['live_url']
                                                    await action.sendGroupPic(group=group, text=t, url=user_info['live_cover'])
                                        else:
                                            t = f"{data[uid]['name']}更新了{k}\n从\n{data[uid][k]}\n更改为\n{v}"
                                            await action.sendGroupText(group=group, text=t)
                                    data[uid][k] = v
                                    # 在每次更新后立即保存，确保消息发送成功后数据被记录
                                    await fileio.write_json(join(resource_path, "data.json"), data)
                            # 再次读取data以获取最新状态，然后处理新动态
                            data = await fileio.read_json(join(resource_path, "data.json"))
                            timeline_row = bm.get_dynamic_list(uid).json()
                            dynamic_id_list, dynamic_data = bm.parse_timeline(timeline_row)
                            if dynamic_id_list is None:
                                raise ValueError(f'tl value error: {timeline_row}')
                            new_dynamics = [t for t in dynamic_id_list if t not in data[uid]['dynamic_id_list']]
                            for ndyid in new_dynamics:
                                ndy = dynamic_data[ndyid]
                                created_at = datetime.fromtimestamp(int(ndy['time']), SHA_TZ)
                                # 超过10分钟的推默认超时, 不再处理
                                now = datetime.now(SHA_TZ)
                                if now - created_at > timedelta(minutes=10):
                                    # 标记为已处理，防止重复
                                    if ndyid not in data[uid]['dynamic_id_list']:
                                        data[uid]['dynamic_id_list'].append(ndyid)
                                    continue
                                for group in subscribes[uid]['groups']:
                                    if ndy['unknown_type']:
                                        t = f"未处理的动态类型: {ndy['unknown_type']}"
                                        await action.sendGroupText(group=group, text=t)
                                    else:
                                        t = ndy['text'] + '\n' + '\n'.join(ndy['links'])
                                        if ndy['imgs']:
                                            await action.sendGroupPic(group=group, text=t, url=ndy['imgs'])
                                        else:
                                            await action.sendGroupText(group=group, text=t)
                                # 发送消息后立即更新该动态的记录，防止异常时重复发送
                                if ndyid not in data[uid]['dynamic_id_list']:
                                    data[uid]['dynamic_id_list'].append(ndyid)
                                await fileio.write_json(join(resource_path, "data.json"), data)
                            data[uid]['dynamic_id_list'] = dynamic_id_list
                            data[uid]['dynamic_data'] = dynamic_data
                            await fileio.write_json(join(resource_path, "data.json"), data)
                        # 调整sleep时间确保API调用频率不超过5次/分钟
                        # 公式：(3 * uid_count) / (300 + uid_count * sleep_time) * 60 ≤ 5
                        # 默认12秒可支持~10个uid订阅
                        await asyncio.sleep(12)
                    except Exception as e:
                        logger.exception(f'bili_dynamic_timeline scheduler error uid: {uid}')
                        t = f'bili_dynamic_timeline scheduler error\nuid: {uid}\ntraceback: {traceback.format_exc()}'
                        # text过长可能发送失败，改为简单提示
                        try: 
                            await action.sendGroupText(group=1014696092, text=t)
                        except:
                            await action.sendGroupText(group=1014696092, text=f'bili_dynamic_timeline scheduler error\nuid: {uid}')
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