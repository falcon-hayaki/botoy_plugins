# -*- coding:utf-8 -*-

from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_MAX_INSTANCES
from pprint import pformat
import logging
import random
from datetime import datetime

bot_qq = 2798046422

# 设置系统变量
os.environ['BOTQQ'] = str(bot_qq)
os.environ['cardSeed'] = str(random.randint(1, 1145141919))
os.system('mkdir -p logs')

bot = Botoy(
    qq = bot_qq,
    use_plugins = True
)
action = Action(
    qq=bot_qq
)


@bot.on_group_msg
def on_group_msg(ctx: GroupMsg):
    # 不处理自身消息
    if ctx.FromUserId == ctx.CurrentQQ:
        return

@deco.ignore_botself
@deco.from_these_groups([1014696092])
@bot.on_group_msg
def manage_plugins(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        if ctx.Content == "重载插件":
            try:
                bot.reload_plugins()
                action.sendGroupText(group=ctx.FromGroupId, content="success")
            except:
                action.sendGroupText(group=ctx.FromGroupId, content="failed")
        if ctx.Content == "加载插件":
            try:
                bot.load_plugins()
                action.sendGroupText(group=ctx.FromGroupId, content="success")
            except:
                action.sendGroupText(group=ctx.FromGroupId, content="failed")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='logs/schedulerLog.txt',
                    filemode='a')

def job_max_instances_listener(event):
    msg = "%s: \n%s\n" % (event.code, pformat(vars(event), indent=4))
    action.sendGroupText(1014696092, msg)
    if event.jobstore != 'default':
        logging.getLogger('apscheduler').info(msg)
    else:
        logging.getLogger('apscheduler').warning(msg)

if __name__ == "__main__":
    from timing import Timing
    timing = Timing()
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    scheduler.add_job(timing.msg_sender, 'cron', second='*/5')
    scheduler.add_job(timing.bili_dynamic, 'cron', minute='*/5', next_run_time=datetime.now())
    scheduler.add_job(timing.bili_live_alarm, 'cron', minute='*/5', next_run_time=datetime.now())
    scheduler.add_job(timing.draw_card_seed, 'cron', minute='*/10')

    scheduler.add_listener(job_max_instances_listener, EVENT_JOB_MAX_INSTANCES)
    scheduler._logger = logging

    scheduler.start()

    bot.run()