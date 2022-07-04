from botoy import Action, EventMsg
from botoy.refine import refine_group_join_event_msg
import os
import json

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

def receive_events(ctx: EventMsg):
    join_ctx = refine_group_join_event_msg(ctx)
    if join_ctx is None or join_ctx.UserID == int(os.getenv('BOTQQ')):
        return
    if join_ctx.FromUin == 1043530960:
        bot.sendGroupText(join_ctx.FromUin, "怀孕")