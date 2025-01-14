import re
import traceback
from dateutil import parser
from botoy import ctx, S, action, jconfig

from . import ym
from utils.tz import SHA_TZ

ytb_video_url_rule = re.compile(r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]+)')

VIDEO_TYPE_TRANS = {
    'none': '视频',
    'live': '直播',
    'upcoming': '直播预约'
}
async def get_ytb_video():
    if msg := ctx.g:
        if msg.text and msg.from_user != jconfig.qq and ytb_video_url_rule.match(msg.text.strip()):
            re_res = ytb_video_url_rule.match(msg.text.strip())
            vid = re_res.groups()[0]
            code, res = ym.get_video_details(vid)
            try:
                if code != 0:
                    raise ValueError(f'get_video_details error: {vid}')
                text = f"{res['name']}的{VIDEO_TYPE_TRANS.get(res['liveBroadcastContent'], res['liveBroadcastContent'])}\n"
                text += f"发布于: {parser.parse(res['publishedAt']).astimezone(SHA_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                text += f"标题: {res['title']}"
                imgs = res['thumbnail']
            except Exception as e:
                text = f'发生未知错误'
                await S.text(text)
                t = f'error in get_ytb_video: group={msg.from_group} text={msg.text}\n'
                t += f'traceback: \n {traceback.format_exc()}'
                await action.sendGroupText(group=1014696092, text=t)
            else:
                await action.sendGroupPic(group=msg.from_group, text=text, url=imgs)