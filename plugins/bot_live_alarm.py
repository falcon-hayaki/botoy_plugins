from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import requests, time

from utils.fileio import read_json, write_json

resource_path = "./resources/bili_live_alarm"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        if ctx.Content == "查看订阅":
            subscribes = read_json(os.path.join(resource_path, "subscribes.json"))
            sub_list = []
            for roomid in subscribes:
                if ctx.FromGroupId in subscribes[roomid]['groups']:
                    uname = get_uname_via_roomid(roomid)
                    if uname == "unexist":
                        bot.sendGroupText(ctx.FromGroupId, "未找到该用户")
                    elif uname == "-412":
                        bot.sendGroupText(ctx.FromGroupId, "牙白！服务器被阿b风控了！")
                    elif uname == "failed":
                        bot.sendGroupText(ctx.FromGroupId, "发生了未预期的错误，出来修bug gkd")
                    else:
                        sub_list.append([uname, roomid])
            if sub_list:
                t = "你群订阅了以下直播间：\n"
                for sub in sub_list:
                    t += sub[0] + "\t" + sub[1] + "\n"
                t = t[:-1]
                bot.sendGroupText(ctx.FromGroupId, t)
            else:
                bot.sendGroupText(ctx.FromGroupId, "见鬼 你群都不看直播的吗('A`)")

        content_list = ctx.Content.strip().split()
        if content_list[0] in ["订阅", "取消订阅"]:
            try:
                int(content_list[1])
            except:
                bot.sendGroupText(ctx.FromGroupId, "请输入正确的room")
            else:
                action = content_list[0]
                roomid = content_list[1]
                uname = get_uname_via_roomid(roomid)
                if uname == "unexist":
                    bot.sendGroupText(ctx.FromGroupId, "未找到该用户")
                elif uname == "-412":
                    bot.sendGroupText(ctx.FromGroupId, "牙白！服务器被阿b风控了！")
                elif uname == "failed":
                    bot.sendGroupText(ctx.FromGroupId, "发生了未预期的错误，叫米白出来修bug gkd")
                else:
                    subscribes = read_json(os.path.join(resource_path, "subscribes.json"))
                    if action == "订阅":
                        if roomid in subscribes:
                            if ctx.FromGroupId in subscribes[roomid]['groups']:
                                t = f"你群已经订阅了{uname}"
                                bot.sendGroupText(ctx.FromGroupId, t)
                            else:
                                subscribes[roomid]['groups'].append(ctx.FromGroupId)
                                t = f"{uname}开播通知订阅成功！"
                                bot.sendGroupText(ctx.FromGroupId, t)
                        else:
                            subscribes[roomid] = {
                                "groups": [ctx.FromGroupId]
                            }
                            t = f"{uname}开播通知订阅成功！"
                            bot.sendGroupText(ctx.FromGroupId, t)
                    if action == "取消订阅":
                        if roomid not in subscribes or ctx.FromGroupId not in subscribes[roomid]["groups"]:
                            t = f"你群未订阅{uname}"
                            bot.sendGroupText(ctx.FromGroupId, t)
                        else:
                            del subscribes[roomid]["groups"][subscribes[roomid]["groups"].index(ctx.FromGroupId)]
                            if not subscribes[roomid]["groups"]:
                                del subscribes[roomid]
                            t = f"你已取消订阅{uname}的开播通知"
                            bot.sendGroupText(ctx.FromGroupId, t)
                    write_json(os.path.join(resource_path, "subscribes.json"), subscribes)

def get_uname_via_roomid(roomid):
    url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={roomid}"
    html = requests.get(url)
    data = json.loads(html.text)
    if data['code'] == -412:
        return "-412"
    elif data["code"] == 1:
        return "unexist"
    elif data["code"] == 0:
        uid = data['data']['uid']
    else:
        return "failed"
    url = f"http://api.bilibili.com/x/web-interface/card?mid={uid}&jsonp=jsonp"
    html = requests.get(url)
    time.sleep(0.5)
    data = json.loads(html.text)
    if data['code'] == -412:
        return "-412"
    elif data["code"] == 1:
        return "unexist"
    elif data["code"] == 0:
        return data["data"]['card']["name"]
    else:
        return "failed"
    