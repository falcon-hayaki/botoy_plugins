from botoy import ctx, S, mark_recv, Action

async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == '一花':
            await S.text("ここっすよ～")
            with Action as action:
                await action.sendGroupText(1014696092, '哈哈')

mark_recv(hello)
