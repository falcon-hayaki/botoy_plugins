from apscheduler.schedulers.background import BackgroundScheduler
from utils.tz import SHA_TZ
scheduler = BackgroundScheduler(timezone=SHA_TZ)

from ._checkin import checkin

def start_scheduler():
    scheduler.start()

def get_scheduler_jobs() -> list:
    return scheduler.get_jobs()




if __name__ == '__main__':
    scheduler = BackgroundScheduler(timezone=SHA_TZ)
    
    @scheduler.scheduled_job('cron', hour='17', minute='*', second='*')
    def test():
        print('test')
        
    print(scheduler.get_jobs())
    scheduler.start()
    
    import time
    while True:
        print(scheduler.get_jobs())
        time.sleep(1)