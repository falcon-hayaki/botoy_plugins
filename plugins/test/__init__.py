from botoy import ctx, S, mark_recv

async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == '一花':
            await S.text("ここっすよ～")

mark_recv(hello)
