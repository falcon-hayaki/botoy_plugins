import random

from botoy import ctx, S, mark_recv, jconfig

async def help_choose():
    if msg := (ctx.g or ctx.f) and msg.from_user != jconfig.qq:
        msg_split = msg.text.strip().split()
        if msg_split and msg_split[0] in ['帮我选', '!c', '！c']:
            await S.text(random.choice(msg_split[1:]) or '')

mark_recv(help_choose)
