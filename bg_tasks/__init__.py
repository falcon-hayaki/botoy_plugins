import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.tz import SHA_TZ
scheduler = AsyncIOScheduler(timezone=SHA_TZ)

from ._checkin import checkin

async def __start_s():
    scheduler.start()
def start_scheduler():
    asyncio.run(__start_s)

def get_scheduler_jobs() -> list:
    return scheduler.get_jobs()
