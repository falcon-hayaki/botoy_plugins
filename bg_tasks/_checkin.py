from botoy import action

from . import scheduler

@scheduler.scheduled_job('cron', hour='17', minute='*', second='*')
def checkin():
    print('test')
    action.sendGroupText(1014696092, '签到')