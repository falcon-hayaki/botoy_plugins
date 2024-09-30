from botoy import ctx, S, mark_recv, jconfig

async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == '一花' and msg.from_user != jconfig.qq:
            await S.text("ここっすよ～")

async def debug():
    if msg := ctx.g:
        if msg.from_group == 1014696092 and msg.from_user != jconfig.qq:
            await S.text('text: {}\nimg: {}\n'.format(msg.text, str(msg.images), msg.msg_type))

mark_recv(hello)
