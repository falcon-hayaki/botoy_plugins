from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import random
import re
import numpy as np
import copy

resource_path_conf = "./resources/draw_card"
resource_path = "./resources/arknights_draw"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

with open(os.path.join(resource_path_conf, 'slow_mode.json'), "rb") as load_f:
    slow_data = json.load(load_f)

with open(os.path.join(resource_path_conf, 'white_list.json'), "rb") as load_f:
    white_list = json.load(load_f)

LEVEL = ['ssr', 'sr', 'r', 'n']

LEVEL_TRANSFORM = {
    'ssr': '★★★★★★',
    'sr': '★★★★★',
    'r': '★★★★',
    'n': '★★★'
}

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == 'TextMsg':
        if ctx.Content[:4] in ['方舟抽卡', '方舟十连']:
            if ctx.FromGroupId not in white_list:
                m = "即日起全面禁抽，并提供戒抽服务。请加群: 183914156。如需添加你群至白名单请联系作者。"
                bot.sendGroupText(ctx.FromGroupId, content=m)
                return
            method = ctx.Content[2:4]
            content = ctx.Content[4:].strip()
            up = []
            use_pool = 'common'
            if content:
                args = content.split()
                if '-i' in args:
                    with open(os.path.join(resource_path, 'user_data.json'), "rb") as load_f:
                        user_data = json.load(load_f)
                    if str(ctx.FromUserId) not in user_data:
                        user_data[str(ctx.FromUserId)] = dict(total_draw=0, last_ssr=0, history=dict(ssr=0, sr=0, r=0, n=0, detail=dict()))
                    user = user_data[str(ctx.FromUserId)]
                    m = '{}的抽卡记录:\n抽卡总数: {}\n连续未出六星次数: {}\n抽卡历史\n六星: {}\n五星: {}\n四星: {}\n三星: {}\n' \
                        .format(ctx.FromNickName, user['total_draw'], user['total_draw'] - user['last_ssr'], \
                                user['history']['ssr'], user['history']['sr'], user['history']['r'], user['history']['n'])
                    if '-a' in args:
                        m += '详细数据: \n'
                        for k, v in user['history']['detail'].items():
                            m += '{}: {}\n'.format(k, v)
                    m = m[:-1]
                    bot.sendGroupText(ctx.FromGroupId, content=m)
                    return
                if '--remake' in args:
                    with open(os.path.join(resource_path, 'user_data.json'), "rb") as load_f:
                        user_data = json.load(load_f)
                    if str(ctx.FromUserId) in user_data:
                        del user_data[str(ctx.FromUserId)]
                    with open(os.path.join(resource_path, 'user_data.json'), "w") as f:
                        json.dump(user_data, f)
                    m = '你已remake'
                    bot.sendGroupText(ctx.FromGroupId, content=m)
                    return
                if '-h' in args:
                    m = '发送`方舟抽卡`或`方舟十连`抽卡，可以在空格后添加附加参数使用不同的功能\n' \
                        + '参数说明\n' \
                        + '-i 查看抽卡历史\n' \
                        + '-a 在-i前提下查看完整干员历史\n' \
                        + '--remake 清空历史\n' \
                        + '-p 选择池子（还在开发中）\n' \
                        + '-up: 选择一个或多个概率up的干员。 例：方舟十连 -up 安洁莉娜 异客\n'
                    bot.sendGroupText(ctx.FromGroupId, content=m)
                    return
                if '-up' in args:
                    up = args[args.index('-up')+1:]
            with open(os.path.join(resource_path, 'user_data.json'), "rb") as load_f:
                user_data = json.load(load_f)
            if str(ctx.FromUserId) not in user_data:
                user_data[str(ctx.FromUserId)] = dict(total_draw=0, last_ssr=0, history=dict(ssr=0, sr=0, r=0, n=0, detail=dict()))
            user = user_data[str(ctx.FromUserId)]
            with open(os.path.join(resource_path, 'pool.json'), "rb") as load_f:
                pool = json.load(load_f)
            pool = pool[use_pool] if use_pool in pool else pool['common']
            rate = pool['rate']
            if method == '抽卡':
                if user['total_draw'] - user['last_ssr'] > 50:
                    for _ in range(user['total_draw'] - user['last_ssr'] - 50):
                        rate['ssr'] += 0.02
                        if rate['n']:
                            rate['n'] -= 0.02
                        elif rate['r']:
                            rate['r'] -= 0.02
                        elif rate['sr']:
                            rate['sr'] -= 0.02
                level_chosen, character = draw_one(pool, rate, up)
                # 更新用户数据
                user['total_draw'] += 1
                if level_chosen == 'ssr':
                    user['last_ssr'] = user['total_draw']
                user['history'][level_chosen] += 1
                if character in user['history']['detail']:
                    user['history']['detail'][character] += 1
                else:
                    user['history']['detail'][character] = 1
                m = '{}抽到了:\n{}\t{}\n当前六星概率: {}'.format(ctx.FromNickName, LEVEL_TRANSFORM[level_chosen], character, rate['ssr'])
                bot.sendGroupText(ctx.FromGroupId, content=m)
            else:
                choices = []
                for _ in range(10):
                    rate = copy.deepcopy(pool['rate'])
                    if user['total_draw'] - user['last_ssr'] > 50:
                        for _ in range(user['total_draw'] - user['last_ssr'] - 50):
                            rate['ssr'] += 0.02
                            if rate['n']:
                                rate['n'] -= 0.02
                            elif rate['r']:
                                rate['r'] -= 0.02
                            elif rate['sr']:
                                rate['sr'] -= 0.02
                    level_chosen, character = draw_one(pool, rate, up)
                    # 更新用户数据
                    user['total_draw'] += 1
                    if level_chosen == 'ssr':
                        user['last_ssr'] = user['total_draw']
                    user['history'][level_chosen] += 1
                    if character in user['history']['detail']:
                        user['history']['detail'][character] += 1
                    else:
                        user['history']['detail'][character] = 1
                    choices.append((level_chosen, character))
                m = '{}抽到了:\n'.format(ctx.FromNickName)
                for level_chosen, character in choices:
                    m += '{}\t{}\n'.format(LEVEL_TRANSFORM[level_chosen], character)
                m += '当前六星概率: {}'.format(rate['ssr'])
                bot.sendGroupText(ctx.FromGroupId, content=m)
            user_data[str(ctx.FromUserId)] = user
            with open(os.path.join(resource_path, 'user_data.json'), "w") as f:
                json.dump(user_data, f)

def draw_one(pool, rate, up):
    p = []
    for level in LEVEL:
        p.append(rate[level])
    p = np.array(p)
    level_chosen = np.random.choice(LEVEL, p=p.ravel())
    up = [x for x in up if x in pool[level_chosen]]
    if up:
        if np.random.rand() < 0.7:
            return level_chosen, random.choice(up)
    return level_chosen, random.choice(pool[level_chosen])