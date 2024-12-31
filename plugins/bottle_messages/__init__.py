import json
from datetime import datetime
from botoy import ctx, S, mark_recv, jconfig, action

from utils.media_processing import download_from_url_and_convert_to_base64
from db import db

async def drop_bottle():
    if msg := ctx.g:
        if msg.text.startswith('扔漂流瓶') and msg.from_user != jconfig.qq:
            bottle_text = msg.text[4:].strip()
            bottle_imgs = []
            if msg.images:
                for img in msg.images:
                    resp_code, img_base64 = download_from_url_and_convert_to_base64(img.Url)
                    if resp_code != 200:
                        continue
                    else:
                        bottle_imgs.append(img_base64)
            if not bottle_text and not bottle_imgs:
                await S.text('好像什么也没有发生...')
                return
            data = dict(
                user_id=msg.from_user,
                user_name=msg.from_user_name,
                group_id=msg.from_group,
                group_name=msg.from_group_name,
                text=bottle_text or '',
                imgs=json.dumps(bottle_imgs),
                time=db.datetime2str(datetime.now())
            )
            db.insert_data('bottle_messages', **data)
            await S.text('漂流瓶已扔出')

async def collect_bottle():
    if msg := ctx.g:
        if msg.text == '捡漂流瓶' and msg.from_user != jconfig.qq:
            bottle_data = db.random_bottle_message(msg.from_group, msg.from_user)
            if not bottle_data:
                await S.text('海里根本没漂流瓶，我漂流瓶呢？')
                return
            else:
                # t = '你捡到了由{}({})从{}({})在{}扔出的漂流瓶，上面写着：\n'.format(
                #     bottle_data['user_name'],
                #     bottle_data['user_id'],
                #     bottle_data['group_name'],
                #     bottle_data['group_id'],
                #     bottle_data['time'],
                # )
                t = '漂流瓶上写着: \n'
                if bottle_data['text']:
                    t += bottle_data['text'].encode("utf-8").decode("unicode_escape")
                try:
                    bottle_imgs = json.loads(bottle_data['imgs'])
                except:
                    bottle_imgs = []
                if bottle_imgs:
                    await action.sendGroupPic(msg.from_group, text=t, base64=bottle_imgs)
                else:
                    await S.text(t)

mark_recv(drop_bottle)
mark_recv(collect_bottle)