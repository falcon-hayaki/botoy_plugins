import re
from dateutil import parser
from botoy import ctx, S, action, jconfig
import logging

from . import xm
from utils.tz import SHA_TZ

logger = logging.getLogger(__name__)

tweet_url_rule = 'https:\\/\\/(?:x|twitter)\\.com\\/[a-zA-Z0-9_]+\\/status\\/([0-9]+).*'

async def get_tweet_withxapi():
    """使用 X API v2 获取推文详情"""
    if msg := ctx.g:
        if msg.text and msg.from_user != jconfig.qq and re.match(tweet_url_rule, msg.text.strip()):
            re_res = re.match(tweet_url_rule, msg.text.strip())
            tid = re_res.groups()[0]
            
            try:
                # 使用 X API v2 获取推文
                res = xm.get_tweet(tid)
                if res.status_code != 200:
                    logger.error(f"Failed to get tweet {tid}: {res.status_code}")
                    return
                
                tweet_json = res.json()
                
                # 解析推文数据
                # parse_tweets 返回 {'tweets': [...], 'meta': {...}}
                parsed_result = xm.parse_tweets(tweet_json)
                
                if not parsed_result or len(parsed_result['tweets']) == 0:
                    logger.warning(f"No tweet data for {tid}")
                    return
                
                tdata = parsed_result['tweets'][0]
                
                # 获取作者信息
                author_info = tdata.get('author')
                if not author_info:
                    logger.warning(f"No author info for tweet {tid}")
                    return
                
                imgs = None
                text = None
                
                # 解析推文内容
                created_at = parser.parse(tdata['created_at']).astimezone(SHA_TZ)
                referenced_tweets = tdata.get('referenced_tweets', [])
                
                if not referenced_tweets:
                    # 普通推文
                    text = f"{author_info['name']}\n发布于{created_at}\n\n{tdata['text']}"
                    imgs = tdata.get('imgs')
                
                elif referenced_tweets[0]['type'] == 'retweeted':
                    # 转推
                    # X API v2 的转推只包含"RT @username: text"格式
                    text = f"{author_info['name']}的转推\n发布于{created_at}\n\n{tdata['text']}"
                    imgs = tdata.get('imgs')
                
                elif referenced_tweets[0]['type'] == 'quoted':
                    # 引用推文
                    text = f"{author_info['name']}的引用转推\n发布于{created_at}\n\n{tdata['text']}"
                    imgs = tdata.get('imgs')
                
                elif referenced_tweets[0]['type'] == 'replied_to':
                    # 回复
                    text = f"{author_info['name']}的回复\n发布于{created_at}\n\n{tdata['text']}"
                    imgs = tdata.get('imgs')
                
                else:
                    # 其他类型
                    text = f"{author_info['name']}\n发布于{created_at}\n\n{tdata['text']}"
                    imgs = tdata.get('imgs')
                
                # 发送消息
                if imgs:
                    await action.sendGroupPic(group=msg.from_group, text=text, url=imgs)
                else:
                    await S.text(text)
                    
            except Exception as e:
                logger.exception(f"Error getting tweet {tid}")
                await S.text('发生未知错误')
