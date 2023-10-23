import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.tz import SHA_TZ
scheduler = AsyncIOScheduler(timezone=SHA_TZ)

from ._checkin import checkin
