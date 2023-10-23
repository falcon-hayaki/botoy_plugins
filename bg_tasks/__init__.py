import asyncio
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.tz import SHA_TZ
scheduler = AsyncIOScheduler(timezone=SHA_TZ)

from ._checkin import checkin

async def scheduler_start():
    scheduler.start()
    while True:
        await asyncio.sleep(0.1)

def __run_event_loop():
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(scheduler_start())
    return

def start_bg():
    threading.Thread(target=__run_event_loop).start()