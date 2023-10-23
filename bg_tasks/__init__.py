from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.tz import SHA_TZ
scheduler = AsyncIOScheduler(timezone=SHA_TZ)

from ._checkin import checkin

async def start_scheduler():
    scheduler.start()

async def get_scheduler_jobs() -> list:
    return scheduler.get_jobs()
