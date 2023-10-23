from apscheduler.schedulers.background import BackgroundScheduler
from utils.tz import SHA_TZ
scheduler = BackgroundScheduler(timezone=SHA_TZ)

from ._checkin import checkin