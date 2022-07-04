from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import requests
import time
import json

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
# @deco.from_these_groups(1014696092)
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType in ['TextMsg', 'AtMsg']:
        if ctx.MsgType == 'AtMsg':
            content = json.loads(ctx.Content)['Content']
        else:
            content = ctx.Content
        if content.strip() == 'moe':
            m = 'http://chacha.hayaki.icu/moe\n使用"moe"或者"发动态"来发布 例：发动态 茶茶真可爱\n*当前处于测试阶段'
            bot.sendGroupText(ctx.FromGroupId, m)
        elif content.split()[0].strip() in ['moe', '发动态']:
            data = bot.getUserInfo(ctx.FromUserId)
            if data['code'] == 0:
                try:
                    icon = data['data']['avatarUrl']
                    nickname = data['data']['nickname']
                    user_id = data['data']['uin']
                except Exception as e:
                    bot.sendGroupText(ctx.FromGroupId, str(repr(e)))
                text = ' '.join(content.strip().split()[1:])
                if not text:
                    return
                timestamp = get_current_time()
                post_data = dict(icon=icon, nickname=nickname, user_id=user_id, text=text, imgs=[], timestamp=timestamp)
                url = 'http://chacha.hayaki.icu/moe'
                m = post(url, post_data)
                bot.sendGroupText(ctx.FromGroupId, m)
            else:
                m = f'error with code: {data["code"]}'
                bot.sendGroupText(ctx.FromGroupId, m)
    elif ctx.MsgType == 'PicMsg':
        content = json.loads(ctx.Content)
        if 'Content' in content and content['Content'].split()[0].strip() in ['moe', '发动态']:
            data = bot.getUserInfo(ctx.FromUserId)
            if data['code'] == 0:
                try:
                    icon = data['data']['avatarUrl']
                    nickname = data['data']['nickname']
                    user_id = data['data']['uin']
                except Exception as e:
                    bot.sendGroupText(ctx.FromGroupId, str(repr(e)))
                text = ' '.join(content['Content'].split()[1:])
                imgs = [img['Url'] for img in content['GroupPic']]
                timestamp = get_current_time()
                post_data = dict(icon=icon, nickname=nickname, user_id=user_id, text=text, imgs=str(imgs), timestamp=timestamp)
                url = 'http://chacha.hayaki.icu/moe'
                m = post(url, post_data)
                bot.sendGroupText(ctx.FromGroupId, m)
            else:
                m = f'error with code: {data["code"]}'
                bot.sendGroupText(ctx.FromGroupId, str(data))

def get_current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def post(url, data):
    try:
        res = requests.post(url=url, data=data)
    except requests.exceptions.RequestException as e:
        return str(repr(e))
    else:
        if res.text == 'success':
            return '已发布\nhttp://chacha.hayaki.icu/moe'
        else:
            return f'发送失败。code: {res.status_code}'
