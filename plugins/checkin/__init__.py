import asyncio
from croniter import croniter
from datetime import datetime, timezone
from botoy import mark_recv, ctx, action

from utils.tz import beijingnow

lock = asyncio.Lock()
crontab = croniter('* * * * *', beijingnow())

async def help_choose():
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab.get_next(datetime):
                await action.sendGroupText(1014696092, '签到')