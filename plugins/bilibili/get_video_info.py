import re
import traceback
from datetime import datetime
from dateutil import parser
from botoy import ctx, S, action, jconfig
import logging

logger = logging.getLogger(__name__)

from . import bm
from utils.tz import SHA_TZ

video_url_rule = r'https:\/\/www\.bilibili\.com\/video\/(BV[a-zA-Z0-9_]+).*'
bv_rule = r'BV[a-zA-Z0-9_]+'

async def get_video_info():
    global video_url_rule, bv_rule
    if msg := ctx.g:
        if msg.text and msg.from_user != jconfig.qq and (re.match(video_url_rule, msg.text.strip()) or re.match(bv_rule, msg.text.strip())):
            video_url_res = re.match(video_url_rule, msg.text.strip())
            bv_res = re.match(bv_rule, msg.text.strip())
            if video_url_res:
                bv = video_url_res.groups()[0]
            elif bv_res:
                bv = msg.text.strip()
            else: 
                return
            try:
                video_info_raw = await bm.get_video_info(bv)
                video_info = bm.parse_video_info(video_info_raw)
                t = f"{video_info['up']}发布于{datetime.fromtimestamp(int(video_info['pubdate'])).strftime('%Y-%m-%d %H:%M:%S%z')}\n"
                t += f"标题：{video_info['title']}\n"
                t += f"简介：{video_info['desc']}\n"
                t += f"观看数：{video_info['view']}\t"
                t += f"弹幕数：{video_info['danmaku']}\t"
                t += f"评论数：{video_info['reply']}\t"
                t += f"点赞：{video_info['like']}\t"
                t += f"投币：{video_info['coin']}\t"
                t += f"收藏：{video_info['favorite']}\t"
                t += f"分享：{video_info['share']}\t"
                await action.sendGroupPic(group=msg.from_group, text=t, url=[video_info['pic']])
            except Exception as e:
                logger.exception(f'get_video_info error bv: {bv}')
                t = f'get_video_info error\bv: {bv}\ntraceback: {traceback.format_exc()}'
                await action.sendGroupText(group=1014696092, text=t)
                