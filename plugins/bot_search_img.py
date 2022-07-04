from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
from pysaucenao import SauceNao
from PicImageSearch import Ascii2D
import asyncio
import requests

resource_path = "./resources/search_img"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
# @deco.from_these_groups(1014696092)
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == 'PicMsg':
        if 'Content' in json.loads(ctx.Content) and json.loads(ctx.Content)['Content'].strip() in ['搜图']:
            ctx.Content = json.loads(ctx.Content)
            url = ctx.Content['GroupPic'][0]['Url']
            imgdata = requests.get(url).content
            with open(os.path.join(resource_path, 'img.jpg'), 'wb') as f:
                f.write(imgdata)
                f.close()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_img_source(ctx.FromGroupId, file=os.path.join(resource_path, 'img.jpg')))
            loop.close()

async def get_img_source(group_id, url=None, file=None):
    api_key = '6b90e0ccbbacae874216be187d5fa706654b1908'
    sauce = SauceNao(api_key=api_key)
    if url is not None:
        results = await sauce.from_url(url)
    elif file is not None:
        results = await sauce.from_file(file)
    else:
        m = None
    if results:
        try:
            m =  results[0].url + '\nresult from saucenao'
        except Exception as e:
            m = "sausenao error: " + str(repr(e))
    else:
        m = get_img_from_ascii2d(file)
    bot.sendGroupText(group_id, m)

def get_img_from_ascii2d(filepath):
    ascii2d = Ascii2D()
    res = ascii2d.search(filepath)
    try:
        return res.raw[1].urls[0] + '\nresult from ascii2d'
    except Exception as e:
        return "ascii2d error: " + str(repr(e))