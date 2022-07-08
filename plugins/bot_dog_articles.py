from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import random

from utils.fileio import read_json

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

resource_path = "./resources/dog_articles"

white_list = read_json(os.path.join(resource_path, "white_list.json"))

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == 'TextMsg':
        if ctx.Content.strip().split()[0] == '定型文':
            if ctx.FromGroupId in white_list:
                l = read_json(os.path.join(resource_path, "data.json"))
                name = (len(ctx.Content.strip().split()) == 1 and '你是谁来着' or ctx.Content.strip().split()[1])
                article = random.choice(l)
                article = article.replace("{name_to_replace}", name)
                bot.sendGroupText(ctx.FromGroupId, article)
            else:
                m = "由于过于刷屏已将该功能禁用。有需求请加群: 183914156，或联系作者添加你群至白名单。"
                bot.sendGroupText(ctx.FromGroupId, content=m)
        elif ctx.Content.strip().split()[0] == '添加定型文' and len(ctx.Content.strip().split()) > 1:
            m = f'定型文添加请求：\nfromGroup:{ctx.fromGroupName}({ctx.FromGroupId})\nfromUser:{ctx.FromNickName}({ctx.fromUserId})\n{ctx.Content}'
            bot.sendFriendText(1511603275, m)
            bot.sendGroupText(ctx.FromGroupId, "已提交")
        elif ctx.Content.strip().split()[0] in ['？定型文', '?定型文']:
            m = "发送 定型文 名字 来随机生成一条定型文，添加定型文 内容 来提交一条新的定型文"
            bot.sendGroupText(ctx.FromGroupId, m)