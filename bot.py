# -*- coding:utf-8 -*-

from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import logging
from logging.handlers import RotatingFileHandler
import random

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

handler = RotatingFileHandler('logs/schedulerLog.txt', 'a', 1024*10, 1, 'utf-8')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[handler])

if __name__ == "__main__":
    from timing import Timing
    
    t= Timing()
    t.start()

    bot.run()