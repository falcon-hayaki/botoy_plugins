from os.path import join

from botoy import ctx, S, mark_recv

resource_path = 'resources/redirection'
from utils import fileio

async def redirection():
    if msg := ctx.f:
        skip_users = await fileio.read_json(join(resource_path, 'skip_users.json'))
        if msg.from_user in skip_users:
            return
        else:
            if msg.text.strip() in ['TD', 'td', '退订', '不再提醒']:
                skip_users.append(msg.from_user)
                await fileio.write_json(join(resource_path, "skip_users.json"), skip_users)
                await S.text('退订成功')
            else:
                await S.text('ハーロー、イチカっすよ～\n有任何问题请加群183914156联系群主\n回复「不再提醒」忽略该消息')
        
mark_recv(redirection)
