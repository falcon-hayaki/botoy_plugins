from botoy import ctx, S, mark_recv

async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == 'hello':
            await S.text("Hello~")

mark_recv(hello)
