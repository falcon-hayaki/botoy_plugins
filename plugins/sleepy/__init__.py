import requests
import base64
from botoy import ctx, S, mark_recv, jconfig, action

from utils.media_processing import download_from_url_and_convert_to_base64

async def sleepy():
    if msg := (ctx.g or ctx.f):
        if msg.text == '#hayaki似了没' and msg.from_user != jconfig.qq:
            url = 'http://127.0.0.1:9010/query'
            resp = requests.get(url)
            print(resp.text)
            if resp.status_code == 200 and resp.json().get('success', False):
                info = resp.json()['info']
                await S.text("hayaki状态: {}\n{}".format(info['name'], info['desc']))
            else:
                await S.text("发生了一点错误喵")

mark_recv(sleepy)
# mark_recv(debug)

