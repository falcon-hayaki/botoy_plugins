import requests
import base64
from botoy import ctx, S, mark_recv, jconfig, action
import logging

logger = logging.getLogger(__name__)

from utils.media_processing import download_from_url_and_convert_to_base64

async def sleepy():
    if msg := (ctx.g or ctx.f):
        if msg.text.lower() in ['#hayaki', 'hayaki状态', 'hayaki似了没'] and msg.from_user != jconfig.qq:
            url = 'http://193.32.151.244:9010/query'
            resp = requests.get(url)
            if resp.status_code == 200 and resp.json().get('success', False):
                info = resp.json()['info']
                await S.text("hayaki状态: {}\n{}".format(info['name'], info['desc']))
            else:
                logger.error("sleepy request failed: %s %s", resp.status_code, resp.text)
                await S.text("发生了一点错误喵")

mark_recv(sleepy)
# mark_recv(debug)

