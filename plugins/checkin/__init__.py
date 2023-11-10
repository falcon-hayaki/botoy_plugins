import asyncio
import copy
from croniter import croniter
from datetime import datetime, timezone
from botoy import mark_recv, ctx, action

from utils.tz import beijingnow

lock = asyncio.Lock()
crontab = croniter('5 0 * * *', beijingnow())
crontab_next = crontab.get_next(datetime)

async def checkin():
    global lock, crontab, crontab_next
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                await action.sendGroupText(1014696092, '签到')
                await action.sendGroupText(856337734, '签到')
                crontab_next = crontab.get_next(datetime)

mark_recv(checkin)