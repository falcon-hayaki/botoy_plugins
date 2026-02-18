import re
import time
from dateutil import parser
from botoy import ctx, S, action, jconfig
from utils.tz import SHA_TZ
from utils.twikit_manager import TwikitManager
import logging

logger = logging.getLogger(__name__)

# Initialize locally
tm = TwikitManager()

tweet_url_rule = r'https:\/\/(?:x|twitter)\.com\/[a-zA-Z0-9_]+\/status\/([0-9]+).*'

# Rate ensuring
last_call_time = 0
INTERVAL = jconfig.get('twitter.twikit_get_tweet_interval', 30)  # Configurable interval

async def get_tweet_by_twikit():
    global last_call_time
    if msg := ctx.g:
        if msg.text and msg.from_user != jconfig.qq and re.match(tweet_url_rule, msg.text.strip()):
            # Rate limit check
            now = time.time()
            if now - last_call_time < INTERVAL:
                logger.warning("get_tweet_by_twikit rate limit hit")
                return 

            re_res = re.match(tweet_url_rule, msg.text.strip())
            tid = re_res.groups()[0]
            
            # Update last call time BEFORE calling to prevent race/spam
            last_call_time = time.time()
            
            try:
                tdata, user_info = tm.get_tweet_detail(tid)
                if not tdata or not user_info:
                    return

                imgs = None
                text = ""
                
                tweet_type = tdata.get('tweet_type', 'default')
                try:
                    created_at = parser.parse(tdata['created_at']).astimezone(SHA_TZ)
                except:
                    created_at = "未知时间"

                if tweet_type == 'default':
                    text = f"{user_info['name']}\n发布于{created_at}\n\n{tdata['text']}"
                    imgs = tdata.get('imgs')
                elif tweet_type == 'retweet':
                    retweet_data = tdata.get('retweet_data', {})
                    r_user = retweet_data.get('user_info', {})
                    r_data = retweet_data.get('data', {})
                    try:
                        origin_created_at = parser.parse(r_data.get('created_at')).astimezone(SHA_TZ)
                    except:
                        origin_created_at = "未知时间"
                    text = f"{user_info['name']}的转推\n转发自:\n{r_user.get('name')}发布于{origin_created_at}\n\n{r_data.get('text')}"
                    imgs = r_data.get('imgs')
                elif tweet_type == 'quote':
                    quote_data = tdata.get('quote_data', {})
                    q_user = quote_data.get('user_info', {})
                    q_data = quote_data.get('data', {})
                    try:
                        origin_created_at = parser.parse(q_data.get('created_at')).astimezone(SHA_TZ)
                    except:
                        origin_created_at = "未知时间"
                    text = f"{user_info['name']}的转推\n发布于{created_at}\n\n{tdata['text']}\n\n转发自:\n{q_user.get('name')}发布于{origin_created_at}\n\n{q_data.get('text')}"
                    imgs = q_data.get('imgs')
                
                if imgs:
                    await action.sendGroupPic(group=msg.from_group, text=text, url=imgs)
                else:
                    await action.sendGroupText(group=msg.from_group, text=text)

            except Exception as e:
                logger.exception("Error in get_tweet_by_twikit")
                await action.sendGroupText(group=msg.from_group, text="发生未知错误")
