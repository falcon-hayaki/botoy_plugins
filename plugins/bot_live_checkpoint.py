from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import requests, time
from datetime import datetime
import pytz

from utils.fileio import read_json, write_json

resource_path = "./resources/bili_live_alarm"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        if ctx.Content[0] in ["【"] and ctx.Content[-1] in ["】"]:
            subscribes = read_json(os.path.join(resource_path, "subscribes.json"))
            live_stat = read_json(os.path.join(resource_path, "bili_live_status.json"))
            for roomid in subscribes:
                if ctx.FromGroupId in subscribes[roomid]["groups"]:
                    if live_stat[roomid]["status"] == 0:
                        pass
                    else:
                        checkpoint = {}
                        checkpoint["time"] = str(datetime.now(tz=pytz.timezone("Asia/Shanghai")))
                        checkpoint["text"] = ctx.Content[1:-1]
                        if 'checkpoints' not in live_stat[roomid]:
                            live_stat[roomid]['checkpoints'] = []
                        live_stat[roomid]['checkpoints'].append(checkpoint)
                        m = f'已记录，当前时间：{str(datetime.strptime(str(checkpoint["time"])[:-6],"%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(str(subscribes[roomid]["start_time"])[:-6],"%Y-%m-%d %H:%M:%S.%f"))}'
                        bot.sendGroupText(ctx.FromGroupId, m)
                        write_json(os.path.join(resource_path, "bili_live_status.json"), live_stat)