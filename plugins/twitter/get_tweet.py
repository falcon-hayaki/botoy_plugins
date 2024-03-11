import re
from dateutil import parser
from botoy import ctx, S, action, jconfig

from . import tm
from utils.tz import SHA_TZ

tweet_url_rule = 'https:\/\/(?:x|twitter)\.com\/[a-zA-Z0-9_]+\/status\/([0-9]+).*'

async def get_tweet():
    if msg := ctx.g and msg.from_user != jconfig.qq:
        if msg.text and re.match(tweet_url_rule, msg.text.strip()):
            re_res = re.match(tweet_url_rule, msg.text.strip())
            tid = re_res.groups()[0]
            res = tm.get_tweet_detail(tid)
            if res.status_code != 200:
                return
            tdata, user_info = tm.parse_tweet_detail(res.json())
            if not tdata:
                return
            imgs = None
            try:
                tweet_type = tdata['tweet_type']
                created_at = parser.parse(tdata['created_at']).astimezone(SHA_TZ)
                if tweet_type == 'default':
                    t = f"{user_info['name']}\n发布于{created_at}\n\n{tdata['text']}"
                    imgs = tdata.get('imgs')
                elif tweet_type == 'retweet':
                    retweet_data = tdata['retweet_data']
                    origin_created_at = parser.parse(retweet_data['data']['created_at']).astimezone(SHA_TZ)
                    t = f"{user_info['name']}的转推\n转发自:\n{retweet_data['user_info']['name']}发布于{origin_created_at}\n\n{retweet_data['data']['text']}"
                    imgs = retweet_data['data'].get('imgs')
                elif tweet_type == 'quote':
                    quote_data = tdata['quote_data']
                    origin_created_at = parser.parse(quote_data['data']['created_at']).astimezone(SHA_TZ)
                    t = f"{user_info['name']}的转推\n发布于{created_at}\n\n{tdata['text']}\n\n转发自:\n{quote_data['user_info']['name']}发布于{origin_created_at}\n\n{quote_data['data']['text']}"
                    imgs = quote_data['data'].get('imgs')
                text = t
                
            except Exception as e:
                imgs = None
                text = f'发生未知错误'
            if imgs:
                await action.sendGroupPic(group=msg.from_group, text=text, url=imgs)
            else:
                await S.text(text)