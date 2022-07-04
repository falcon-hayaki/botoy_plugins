from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import requests
from bs4 import BeautifulSoup
import time

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        if 'twitter.com' and 'status' in ctx.Content.strip().split(sep='/'):
            print("test")
            split_list = ctx.Content.strip().split(sep='/')
            tw_id = split_list[split_list.index('status') + 1]
            msg, img = get_tweet(tw_id)
            if msg == 'tw_id_error':
                bot.sendGroupText(ctx.FromGroupId, msg)
            else:
                bot.sendGroupText(ctx.FromGroupId, msg)
                if img:
                    time.sleep(0.3)
                    bot.sendGroupPic(ctx.FromGroupId, picUrl = img)

def get_tweet(tw_id):
    url = f"https://twitter.com/momosuzunene/status/{tw_id}"
    user_agent_old_phone = 'Nokia5310XpressMusic_CMCC/2.0 (10.10) Profile/MIDP-2.1 '\
    'Configuration/CLDC-1.1 UCWEB/2.0 (Java; U; MIDP-2.0; en-US; '\
    'Nokia5310XpressMusic) U2/1.0.0 UCBrowser/9.5.0.449 U2/1.0.0 Mobile'
    headers = { 'User-Agent': user_agent_old_phone}

    html = requests.get(url, headers=headers)
    soup = BeautifulSoup(html.content, 'html.parser')

    try:
        main_tweet=soup.find('div', class_='tweet-detail')
    except:
        return ["tw_id_error", ""]
    else:
        name = main_tweet.find('div', class_='fullname').get_text().strip()
        reply = ':\n'
        try:
            reply += main_tweet.find('span', class_='tweet-reply-context username').get_text().strip() + '\n'
        except:
            pass
        finally:
            tw = main_tweet.find('div', class_='tweet-text')
            text = tw.find('div', class_='dir-ltr').get_text().strip()
            media = main_tweet.find('div', class_='media')
            if not media:
                return [name + reply + text, '']
            else:
                img_l = media.find('img')['src'].split(sep=':')
                img = img_l[0] + ':' + img_l[1]
                return [name + reply + text, img]