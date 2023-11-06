import asyncio
from croniter import croniter
from datetime import datetime, timezone
from botoy import mark_recv, ctx, action

from utils.tz import beijingnow

lock = asyncio.Lock()
crontab = croniter('* * * * *', beijingnow())
next_check_time = crontab.get_next(datetime)
print(type(next_check_time), next_check_time)
test1 = datetime.now()
test2 = '123'

async def checkin():
    print(test1)
    print(test2)
    print(next_check_time)
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= next_check_time:
                await action.sendGroupText(1014696092, '签到')
                next_check_time = crontab.get_next(datetime)

mark_recv(checkin)