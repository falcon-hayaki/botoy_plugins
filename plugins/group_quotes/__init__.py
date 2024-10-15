import json
from datetime import datetime
from botoy import ctx, S, mark_recv, jconfig, action

from utils.media_processing import download_from_url_and_convert_to_base64
from db import db

async def save_quote():
    if msg := ctx.g:
        if msg.text.startswith('/save') and msg.from_user != jconfig.qq:
            user_key = msg.text[5:].strip()
            if not msg.images:
                return
            img = msg.images[0]
            resp_code, img_base64 = download_from_url_and_convert_to_base64(img.Url)
            if resp_code != 200:
                return
            data = dict(
                user_key=user_key,
                group_id=msg.from_group,
                img=img_base64,
                time=db.datetime2str(datetime.now())
            )
            db.insert_data('quotes', **data)
            await S.text('保存成功')

async def get_random_quote():
    if msg := ctx.g:
        if msg.text.startswith('/quote') and msg.from_user != jconfig.qq:
            user_key = msg.text[6:].strip()
            quote_data = db.random_quote(msg.from_group, user_key)
            if not quote_data:
                await S.text('没找到怪话喵！')
                return
            await action.sendGroupPic(msg.from_group, base64=quote_data['img'])

mark_recv(save_quote)
mark_recv(get_random_quote)