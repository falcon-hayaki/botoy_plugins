from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import time

from utils.fileio import read_json, write_json

resource_path = "./resources/pigeon"

bot = Action(
    qq=int(os.getenv('BOTQQ')),
    timeout=200
)

groups = read_json(os.path.join(resource_path, "group_list.json"))
bans = read_json(os.path.join(resource_path, "ban_list.json"))


@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        if ctx.Content in ["list", "群列表"]:
            m = ""
            for group in groups:
                m += group + "\n"
            bot.sendGroupText(ctx.FromGroupId, content=m)
            return
        elif ctx.Content == "组间通信":
            m = "发送 list/群列表 查看支持通信的群\n格式：送信给/发送给[群名]说[要说的话] （不用加上中括号）"
            bot.sendGroupText(ctx.FromGroupId, content=m)
            return
    msg_format = format_content(ctx)
    print(msg_format)
    # msg_format[0]: to_group, msg_format[1]: msg, msg_format[2]: pic_url
    if not msg_format[0]:
        if not msg_format[1]:
            return
        else:
            bot.sendGroupText(ctx.FromGroupId, content=msg_format[1])
    else:
        from_group = ""
        if msg_format[0] == "test_group":
            from_group = ctx.FromGroupName
        else:
            for group in groups:
                if groups[group] == ctx.FromGroupId:
                    from_group = group
                    break
        if from_group:
            if msg_format[0] not in bans or (msg_format[0] in bans and ctx.FromUserId not in bans[msg_format[0]]):
                if ctx.MsgType == 'TextMsg':
                    m_from = "已发送"
                    m_to = f"你收到一条来自 {from_group} 的 {ctx.FromNickName}({ctx.FromUserId}) 发来的消息：\n{msg_format[1]}"
                    bot.sendGroupText(groups[msg_format[0]], content=m_to)
                    bot.sendGroupText(ctx.FromGroupId, content=m_from)
                elif ctx.MsgType == 'PicMsg':
                    m_from = "已发送"
                    m_to = f"来自 {from_group} 的 {ctx.FromNickName}({ctx.FromUserId}) 发来的消息:\n{msg_format[1]}[PICFLAG]"
                    send_stat = {}
                    count = 0
                    while not send_stat:
                        send_stat = bot.sendGroupPic(groups[msg_format[0]], content=m_to, picUrl=msg_format[2])
                        count += 1
                        if count == 5:
                            m_from = "发送超时失败"
                            break
                    print(send_stat)
                    bot.sendGroupText(ctx.FromGroupId, content=m_from)
        else:
            m = "你群未在群列表，需要添加至列表请联系mami或送信给test_group"
            bot.sendGroupText(ctx.FromGroupId, content=m)
        
def format_content(ctx):
    to_group = ""
    msg = ""
    pic_url = ""
    text = ""
    if ctx.MsgType == 'TextMsg':
        text = ctx.Content
    elif ctx.MsgType == 'PicMsg':
        content = json.loads(ctx.Content)
        if "Content" in content:
            text = content["Content"]
            pic_url = content["GroupPic"][0]["Url"]
    if text[0:3] in ["送信给", "发送给"]:
        text = text[3:].strip()
        for group in groups:
            if group in text and text.index(group) == 0:
                to_group = group
                break
        if to_group == "":
            return ["", "未找到群"]
        else:
            text = text[len(to_group):].strip()
            if text[0] == "说":
                msg = text[1:]
                return [to_group, msg.strip(), pic_url]
            else:
                return ["", "格式有误"]
    else:
        return ["", ""]