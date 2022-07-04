from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import random

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == 'TextMsg':
        content_list = ctx.Content.strip().split()
        if content_list[0] in ["帮我选", "!c", "！c"]:
            chosen = random.choice(content_list[1:])
            bot.sendGroupText(ctx.FromGroupId, content=chosen)