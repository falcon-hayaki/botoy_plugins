from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import requests, time
from datetime import datetime
import pytz

resource_path = "./resources/bili_live_checkpoint"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        if ctx.Content[0] in ["【"] and ctx.Content[-1] in ["】"]:
            with open(os.path.join(resource_path, "subscribes.json"), 'rb') as f:
                subscribes = json.load(f)
            for roomid in subscribes:
                if ctx.FromGroupId in subscribes[roomid]["groups"]:
                    if subscribes[roomid]["status"] == 0:
                        m = roomid + "当前未开播"
                        bot.sendGroupText(ctx.FromGroupId, m)
                    else:
                        checkpoint = {}
                        checkpoint["time"] = str(datetime.now(tz=pytz.timezone("Asia/Shanghai")))
                        checkpoint["text"] = ctx.Content[1:-1]
                        with open(os.path.join(resource_path, "checkpoints.json"), "rb") as f:
                            checkpoints = json.load(f)
                        checkpoints[roomid].append(checkpoint)
                        with open(os.path.join(resource_path, "checkpoints.json"), "w") as f:
                            json.dump(checkpoints, f)
                        m = f'已记录，当前时间：{str(datetime.strptime(str(checkpoint["time"])[:-6],"%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(str(subscribes[roomid]["start_time"])[:-6],"%Y-%m-%d %H:%M:%S.%f"))}'
                        bot.sendGroupText(ctx.FromGroupId, m)