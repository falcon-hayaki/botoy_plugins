from os.path import join
import random
from datetime import datetime
from pytz import timezone

from botoy import ctx, S, mark_recv, file_to_base64

resource_path = 'resources/hanayori_fortune'
from utils import fileio
from .draw import Draw

async def hanayori_fortune():
    if msg := ctx.g:
        print('test1')
        if msg.text.strip() in ['抽签', '抽签签']:
            print('test2')
            texts = await fileio.read_json(join(resource_path, 'fortune/copywriting.json'))
            titles = await fileio.read_json(join(resource_path, 'fortune/goodLuck.json'))
            now = datetime.now(tz=timezone("Asia/Shanghai"))
            seed = int(''.join([str(i) for i in [now.year, now.month, now.day, ctx.from_user]]))
            random.seed(seed)
            choice = random.choice(range(1, 12))
            random.seed(seed)
            text = random.choice(texts['copywriting'])
            for title in titles["types_of"]:
                if title["good-luck"] == text["good-luck"]:
                    break
            text = text["content"]
            title = title["name"]
            pic_chosen = join(resource_path, 'img/frame_{}.png'.format(choice))
            pic_path = await Draw.draw_card(pic_chosen, title, text, ctx.from_group)
            await S.image(data=file_to_base64(pic_path), text='今天的运势是', at=ctx.from_user)
            
mark_recv(hanayori_fortune)