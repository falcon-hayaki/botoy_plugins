from botoy import ctx, S, mark_recv, jconfig

async def hello():
    if msg := (ctx.g or ctx.f) and msg.from_user != jconfig.qq:
        if msg.text == '一花':
            await S.text("ここっすよ～")

mark_recv(hello)
