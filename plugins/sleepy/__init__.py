import requests
import base64
from botoy import ctx, S, mark_recv, jconfig, action

from utils.media_processing import download_from_url_and_convert_to_base64

async def sleepy():
    if msg := (ctx.g or ctx.f):
        if msg.text.lower() in ['#hayaki', 'hayaki状态', 'hayaki似了没'] and msg.from_user != jconfig.qq:
            url = 'http://sleepy.hayaki.icu/query'
            resp = requests.get(url)
            if resp.status_code == 200 and resp.json().get('success', False):
                info = resp.json()['info']
                await S.text("hayaki状态: {}\n{}".format(info['name'], info['desc']))
            else:
                await S.text("发生了一点错误喵")

mark_recv(sleepy)
# mark_recv(debug)

