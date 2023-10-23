from botoy import action

from . import scheduler

@scheduler.scheduled_job('cron', second='*/2')
def checkin():
    action.sendGroupText(1014696092, '签到')