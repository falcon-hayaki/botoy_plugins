from botoy import ctx, S, mark_recv, action

async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == '一花':
            await S.text("ここっすよ～")
            await action.sendGroupText(1014696092, '哈哈')

mark_recv(hello)
