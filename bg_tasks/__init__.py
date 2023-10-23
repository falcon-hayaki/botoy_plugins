import asyncio
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.tz import SHA_TZ
scheduler = AsyncIOScheduler(timezone=SHA_TZ)

from ._checkin import checkin

def __scheduler_start():
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(scheduler.start())
    return

def start_bg():
    threading.Thread(target=__scheduler_start).start()