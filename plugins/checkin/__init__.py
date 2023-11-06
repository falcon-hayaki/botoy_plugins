import asyncio
import copy
from croniter import croniter
from datetime import datetime, timezone
from botoy import mark_recv, ctx, action

from utils.tz import beijingnow

lock = asyncio.Lock()
crontab = croniter('* * * * *', beijingnow())
crontab_next = None
test1 = datetime.utcnow()
test2 = '123'
test3 = beijingnow()

async def checkin():
    print(test1)
    print(test2)
    print(test3)
    print(crontab_next)
    if msg := ctx.g and not lock.locked():
        async with lock:
            if crontab_next is None or beijingnow() >= crontab_next:
                await action.sendGroupText(1014696092, '签到')
                crontab_next = crontab.get_next(datetime)

mark_recv(checkin)