from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import random

from utils.fileio import read_json, write_json

resource_path = "./resources/draw_card"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

cardpool = ["R"] * 789 + ["SR"] * 200 + ["SSR"] * 10 + ["SP"] * 1 + ["N"] * 10
slow_data = read_json(os.path.join(resource_path, "slow_mode.json"))
white_list = read_json(os.path.join(resource_path, "white_list.json"))

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == 'TextMsg':
        if ctx.Content[:4] in ['方舟抽卡', '方舟十连']:
            return
        if ctx.FromGroupId not in white_list:
            if ctx.Content in ["抽卡", "单抽", "十连", "十连抽"]:
                m = "请加群: 183914156 联系作者添加你群至白名单。"
                bot.sendGroupText(ctx.FromGroupId, content=m)
        elif "抽卡群" not in ctx.Content and ("抽卡" in ctx.Content or "单抽" in ctx.Content or "十连" in ctx.Content):
            roles = read_json(os.path.join(resource_path, "cards.json"))
                
            if ctx.FromGroupId in slow_data["groups"]:
                slow_mode(ctx)
            elif "原神" in ctx.Content:
                pool = ["R"] * 943 + ["SR"] * 51 + ["SSR"] * 6
                rarity = {"SSR": "★★★★★", "SR": "★★★★", "R": "★★★"}
                if '抽卡' in ctx.Content or "单抽" in ctx.Content:
                    selection = random.choice(pool)
                    name = random.choice(roles["原神"][selection])
                    msg = f"{rarity[selection]}\t{name}"
                    bot.sendGroupText(ctx.FromGroupId, content=msg)
                elif '十连' in ctx.Content:
                    msg = ""
                    selections = []
                    for _ in range(10):
                        selection = random.choice(pool)
                        if len(selections) == 9:
                            if "SR" not in selections and "SSR" not in selections:
                                selection = "SR"
                        selections.append(selection)
                        msg += rarity[selection] + "\t" + random.choice(roles["原神"][selection]) + "\n"
                    msg += "注：无武器无UP无保底，三星只有以理服人"
                    bot.sendGroupText(ctx.FromGroupId, content=msg)
            elif '抽卡' in ctx.Content or "单抽" in ctx.Content:
                if IsMsgFromBot(ctx.FromUserId):
                    bot.sendGroupText(ctx.FromGroupId, content="你抽nm呢？")
                    return
                selection = random.choice(cardpool)
                name = random.choice(roles[selection])
                msg = f'{selection}\t{name}'
                bot.sendGroupText(ctx.FromGroupId, content=msg)
            elif '十连' in ctx.Content:
                if IsMsgFromBot(ctx.FromUserId):
                    bot.sendGroupText(ctx.FromGroupId, content="你抽nm呢？")
                    return
                msg = ""
                for _ in range(10):
                    selection = random.choice(cardpool)
                    msg += selection + "\t" + random.choice(roles[selection]) + "\n"
                bot.sendGroupText(ctx.FromGroupId, content=msg)
    if ctx.Content.strip().split(sep = " ")[0] == "添加卡" and len(ctx.Content.strip().split(sep = " ")) == 3:
        add_to_pool(ctx, ctx.Content.strip().split(sep = " ")[1], ctx.Content.strip().split(sep = " ")[2])
        

def add_to_pool(ctx, rarity, name):
    roles = read_json(os.path.join(resource_path, "cards.json"))
    if rarity in roles:
        if name not in roles[rarity]:
            if ctx.FromGroupId == 1014696092:
                roles[rarity].append(name)
                write_json(os.path.join(resource_path, 'cards.json'), roles)
                bot.sendGroupText(ctx.FromGroupId, content="添加成功")
            else:
                m = f"卡池添加申请：\n{rarity}\t{name}\nfromGroup:{ctx.FromGroupName}\nfromUser:{ctx.FromNickName}\n添加卡 {rarity} {name}"
                bot.sendGroupText(1014696092, content=m)
        else:
            m = f"已存在{name}"
            bot.sendGroupText(ctx.FromGroupId, content=m)
    else:
        bot.sendGroupText(ctx.FromGroupId, content="请检查格式（注：稀有度为大写）")

def slow_mode(ctx):
    current_seed = int(os.getenv('cardSeed'))
    roles = read_json(os.path.join(resource_path, "cards.json"))

    if slow_data["seed"] != current_seed:
        slow_data["seed"] = current_seed
        slow_data["single_users"] = []
        slow_data["ten_users"] = []

    if '抽卡' in ctx.Content:
        if ctx.FromUserId in slow_data["single_users"]:
            bot.sendGroupText(ctx.FromGroupId, content="冷却中")
            return
        slow_data["single_users"].append(ctx.FromUserId)

        if IsMsgFromBot(ctx.FromUserId):
            bot.sendGroupText(ctx.FromGroupId, content="你抽nm呢？")
            return

        random.seed(slow_data["seed"] + ctx.FromUserId)
        selection = random.choice(cardpool)
        random.seed(slow_data["seed"] + ctx.FromUserId)
        name = random.choice(roles[selection])
        msg = f'{selection}\t{name}'
        bot.sendGroupText(ctx.FromGroupId, content=msg)
    elif '十连' in ctx.Content:
        if ctx.FromUserId in slow_data["ten_users"]:
            bot.sendGroupText(ctx.FromGroupId, content="冷却中")
            return
        slow_data["ten_users"].append(ctx.FromUserId)

        if IsMsgFromBot(ctx.FromUserId):
            bot.sendGroupText(ctx.FromGroupId, content="你抽nm呢？")
            return

        msg = ""
        for i in range(10):
            random.seed((slow_data["seed"] + ctx.FromUserId) * (i + 2))
            selection = random.choice(cardpool)
            random.seed((slow_data["seed"] + ctx.FromUserId) * (i + 2))
            msg += selection + "\t" + random.choice(roles[selection]) + "\n"
        bot.sendGroupText(ctx.FromGroupId, content=msg)

    write_json(os.path.join(resource_path, 'slow_mode.json'), slow_data)

def IsMsgFromBot(QQid):
    if QQid in [2578353087]:
        return True
    else:
        return False