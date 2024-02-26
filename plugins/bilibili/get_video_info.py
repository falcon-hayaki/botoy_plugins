import re
import traceback
from datetime import datetime
from dateutil import parser
from botoy import ctx, S, action

from . import bm
from utils.tz import SHA_TZ

video_url_rule = 'https:\/\/www\.bilibili\.com\/video\/(BV[a-zA-Z0-9_]+).*'
bv_rule = 'BV[a-zA-Z0-9_]+'

async def get_video_info():
    global video_url_rule, bv_rule
    if msg := ctx.g:
        if msg.text and msg.from_group == 1014696092 and (re.match(video_url_rule, msg.text.strip()) or re.match(bv_rule, msg.text.strip())):
            video_url_rule = re.match(video_url_rule, msg.text.strip())
            bv_rule = re.match(bv_rule, msg.text.strip())
            if video_url_rule:
                bv = video_url_rule.groups()[0]
            elif bv_rule:
                bv = msg.text.strip()
            try:
                video_info = bm.parse_video_info(bm.get_video_info(bv).json())
                t = f"{video_info['owner']}发布于{datetime.fromtimestamp(video_info['pubdate']).strftime('%Y-%m-%d %H:%M:%S%z')}\n"
                t += f"标题：{video_info['title']}\n链接：{video_info['desc']}\n"
                t += f"简介：{video_info['desc']}\n"
                await action.sendGroupPic(group=msg.from_group, text=t, url=[video_info['pic']])
            except Exception as e:
                print(e, traceback.format_exc())
                t = f'get_video_info error\bv: {bv}\ntraceback: {traceback.format_exc()}'
                await action.sendGroupText(group=1014696092, text=t)
                