import asyncio
import copy
from croniter import croniter
from datetime import datetime, timezone
from botoy import mark_recv, ctx, action

from utils.tz import beijingnow

lock = asyncio.Lock()
crontab = croniter('* * * * *', beijingnow())
crontab_next = copy.deepcopy(crontab.get_next(datetime))
print(type(crontab_next), crontab_next)
test1 = datetime.utcnow()
test2 = '123'
test3 = beijingnow()
test4 = copy.deepcopy(crontab.get_next(datetime))

async def checkin():
    print(test1)
    print(test2)
    print(test3)
    print(test4)
    print(crontab_next)
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                await action.sendGroupText(1014696092, '签到')
                crontab_next = crontab.get_next(datetime)

mark_recv(checkin)