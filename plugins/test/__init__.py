import requests
import base64
from botoy import ctx, S, mark_recv, jconfig, action
import logging
logger = logging.getLogger(__name__)

from utils.media_processing import download_from_url_and_convert_to_base64

async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == '一花' and msg.from_user != jconfig.qq:
            await S.text("ここっすよ～")

async def debug():
    if msg := ctx.g:
        if msg.from_group == 1014696092 and msg.from_user != jconfig.qq:
            if msg.images:
                img_base64_list = []
                for img in msg.images:
                    resp_code, img_base64 = download_from_url_and_convert_to_base64(img.Url)
                    if resp_code != 200:
                        await S.text('发送失败')
                        await action.sendGroupText(1014696092, 'err code: {}, text: {}'.format(resp_code, img_base64))
                        return
                    else:
                        img_base64_list.append(img_base64)
                await action.sendGroupPic(msg.from_group, text=msg.text, base64=img_base64_list)
            else:
                # await S.text(msg.text)
                logger.info('debug text: %s', str(ctx.data))
                # action.sendGroupText(msg.from_group, msg.text, atUserNick=)

mark_recv(hello)
mark_recv(debug)

