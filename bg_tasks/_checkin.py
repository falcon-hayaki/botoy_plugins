from botoy import action, sync_run

from . import scheduler

@scheduler.scheduled_job('cron', hour='*', minute='*', second='*/5')
def checkin():
    sync_run(action.sendGroupText(1014696092, '签到'))