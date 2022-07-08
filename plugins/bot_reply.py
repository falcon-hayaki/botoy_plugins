import imp
from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import re
import random

from utils.fileio import read_json, write_json

resource_path = "./resources/reply"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

data = dict()

data = read_json(os.path.join(resource_path, 'data.json'))

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    global data
    if ctx.MsgType == "TextMsg":
        groupid = str(ctx.FromGroupId)
        if ctx.Content in ["!help", "！help"]:
            m = ('1. 说key答value，将会添加一条新的回复规则\n'
                '2. !list，列出当前回复规则\n'
                '3. !删除(或!del)+序号，删除对应的规则。删除多个用空格隔开\n'
                '4. !clear，清空列表\n'
                '5. 触发条件为全匹配，支持正则表达式\n'
                '6. 当前仅只支持纯文本消息\n'
                '7. 支持使用()捕获匹配，在回答中加入{}或{[序号]}替换捕获到的匹配（多个捕获将按顺序替换）。\n'
                    '例1：说不许(.*)答不许不许{}\n'
                    '例2：说(.*)茶茶(.*)答{0}llgl{1} 或 说(.*)茶茶(.*)答{}llgl{}\n'
                )
            bot.sendGroupText(ctx.FromGroupId, content=m)
        elif ctx.Content in ['!clear', '！clear', '！清空', '!清空']:
            if groupid in data:
                data[groupid].clear()
                write_json(os.path.join(resource_path, 'data.json'), data)
            bot.sendGroupText(ctx.FromGroupId, content="已清空")
        elif ctx.Content in ["!list", "！list"]:
            data = read_json(os.path.join(resource_path, 'data.json'))
            if groupid not in data or not data[groupid]:
                bot.sendGroupText(ctx.FromGroupId, content="列表为空")
            else:
                count = 1
                m = ""
                for key in data[groupid]:
                    for value in data[groupid][key]:
                        m += f"{count}. key={key}, value={value}\n"
                        count += 1
                bot.sendGroupText(ctx.FromGroupId, content=m)
        elif re.match("说.{1,}答.{1,}", ctx.Content) is not None:
            data = read_json(os.path.join(resource_path, 'data.json'))
            key = ctx.Content[1:2+ctx.Content[2:].index("答")].strip()
            value = ctx.Content[3+ctx.Content[2:].index("答"):].strip()
            if groupid not in data:
                data[groupid] = dict()
            if key not in data[groupid]:
                data[groupid][key] = list()
            if value in data[groupid][key]:
                m = "已存在"
            else:
                data[groupid][key].append(value)
                m = f"已添加: key={key}, value={value}"
                write_json(os.path.join(resource_path, 'data.json'), data)
            bot.sendGroupText(ctx.FromGroupId, content=m)
        elif re.match("(?:!|！)(?:删除|del)[ ]+[0-9 ]+$", ctx.Content) is not None:
            data = read_json(os.path.join(resource_path, 'data.json'))
            del_list = ctx.Content.strip().split()[1:]
            if groupid not in data:
                data[groupid] = dict()
            if not data[groupid]:
                bot.sendGroupText(ctx.FromGroupId, content="列表为空")
                return
            else:
                count = 1
                m = '已删除：\n'
                key_to_del = []
                for key in data[groupid]:
                    for value in data[groupid][key]:
                        if str(count) in del_list:
                            data[groupid][key].remove(value)
                            if not data[groupid][key]:
                                key_to_del.append(key)
                            m += f"key={key}, value={value}\n"
                        count += 1
                for key in key_to_del:
                    del data[groupid][key]
                write_json(os.path.join(resource_path, 'data.json'), data)
                bot.sendGroupText(ctx.FromGroupId, content=m)
        elif groupid in data:
            matched = []
            for key in data[groupid]:
                result = re.match(f"{key}$", ctx.Content)
                if result is not None:
                    matched.append(dict(key=key, result=result))
            if matched:
                selection = random.choice(matched)
                key = selection['key']
                result = selection['result']
                text = random.choice(data[groupid][key])
                try:
                    text = text.format(*result.groups())
                except:
                    bot.sendGroupText(ctx.FromGroupId, content="发生越界错误")
                    return
                bot.sendGroupText(ctx.FromGroupId, content=text)