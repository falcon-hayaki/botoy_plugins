from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import requests, time

from utils.fileio import read_json, write_json

resource_path = "./resources/bili_dynamic"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        if ctx.Content == "查看关注":
            subscribes = read_json(os.path.join(resource_path, "subscribes_list.json"))
            sub_list = []
            for uid in subscribes:
                if ctx.FromGroupId in subscribes[uid]['groups']:
                    info = get_up_info(uid)
                    if info["code"] == -412:
                        bot.sendGroupText(ctx.FromGroupId, "牙白！服务器被阿b风控了！")
                        return
                    uname = info['data']['name']
                    sub_list.append([uname, uid])
            if sub_list:
                t = "你群关注了：\n"
                for sub in sub_list:
                    t += sub[0] + "\t" + sub[1] + "\n"
                t = t[:-1]
                bot.sendGroupText(ctx.FromGroupId, t)
            else:
                bot.sendGroupText(ctx.FromGroupId, "你群什么也没有关注('A`)")

        content_list = ctx.Content.strip().split()
        if content_list[0] in ["关注", "取消关注"]:
            try:
                int(content_list[1])
            except:
                bot.sendGroupText(ctx.FromGroupId, "请输入正确的uid")
            else:
                action = content_list[0]
                uid = content_list[1]
                info = get_up_info(uid)
                if info["code"] == -404:
                    bot.sendGroupText(ctx.FromGroupId, "未找到该用户")
                elif info["code"] == -412:
                    bot.sendGroupText(ctx.FromGroupId, "牙白！服务器被阿b风控了！")
                elif info["code"] == 0:
                    subscribes = read_json(os.path.join(resource_path, "subscribes_list.json"))
                    uname = info['data']['name']
                    if action == "关注":
                        if uid in subscribes:
                            if ctx.FromGroupId in subscribes[uid]['groups']:
                                t = f"你群已经关注了{uname}"
                                bot.sendGroupText(ctx.FromGroupId, t)
                            else:
                                subscribes[uid]['groups'].append(ctx.FromGroupId)
                                t = f"{uname}关注成功！"
                                bot.sendGroupText(ctx.FromGroupId, t)
                        else:
                            subscribes[uid] = {
                                "groups": [ctx.FromGroupId]
                            }
                            t = f"{uname}关注成功！"
                            bot.sendGroupText(ctx.FromGroupId, t)
                    if action == "取消关注":
                        if uid not in subscribes or ctx.FromGroupId not in subscribes[uid]["groups"]:
                            t = f"你群未关注{uname}"
                            bot.sendGroupText(ctx.FromGroupId, t)
                        else:
                            del subscribes[uid]["groups"][subscribes[uid]["groups"].index(ctx.FromGroupId)]
                            if not subscribes[uid]["groups"]:
                                del subscribes[uid]
                            t = f"你已取消关注{uname}"
                            bot.sendGroupText(ctx.FromGroupId, t)
                    write_json(os.path.join(resource_path, "subscribes_list.json"), subscribes)

def get_up_info(uid):
    url = f"http://api.bilibili.com/x/web-interface/card?mid={uid}&jsonp=jsonp"
    html = requests.get(url)
    time.sleep(0.5)
    data = json.loads(html.text)
    return data