from botoy import ctx, S, mark_recv, jconfig

async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == '一花' and msg.from_user != jconfig.qq:
            await S.text("ここっすよ～")

async def debug():
    if msg := ctx.g:
        if msg.from_group == 1014696092 and msg.from_user != jconfig.qq:
            if msg.images:
                await S.image([img.FileMd5 for img in msg.images], text=msg.text)
            else:
                await S.text(msg.text)

mark_recv(hello)
mark_recv(debug)
