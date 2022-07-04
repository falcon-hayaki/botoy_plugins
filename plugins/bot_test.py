from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.FromGroupId == 1014696092:
        if ctx.MsgType == 'TextMsg':
            bot.sendGroupText(ctx.FromGroupId, str(bot.getUserInfo(ctx.FromUserId)))
    pass
