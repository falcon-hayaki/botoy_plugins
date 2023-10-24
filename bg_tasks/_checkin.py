from botoy import action, sync_run

from . import scheduler

@scheduler.scheduled_job('cron', hour='0', minute='5', second='0')
def checkin():
    try:
        sync_run(action.sendGroupText(1014696092, '签到'))
    except:
        pass