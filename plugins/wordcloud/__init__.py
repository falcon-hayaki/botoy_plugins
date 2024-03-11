import asyncio
import copy
import json
import requests
import traceback
from os.path import join, exists
from os import system
from croniter import croniter
from datetime import datetime, timezone
import jieba
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
from botoy import mark_recv, ctx, action, file_to_base64, jconfig

resource_path = 'resources/wordcloud'
from utils.tz import beijingnow
from utils import fileio

system(f"mkdir -p {join(resource_path, 'chat_history')}")
system(f"mkdir -p {join(resource_path, 'group_wordcloud')}")

lock = asyncio.Lock()
crontab = croniter('5 0 * * *', beijingnow())
# crontab = croniter('*/2 * * * *', beijingnow())
crontab_next = crontab.get_next(datetime)

with open(join(resource_path, 'group_enable.json'), 'r') as f:
    group_enable = json.load(f)

async def gen_wordcloud():
    global lock, crontab, crontab_next, group_enable
    if msg := ctx.g and msg.from_user != jconfig.qq and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                # 停用词
                stopwords = set()
                t = requests.get('https://raw.githubusercontent.com/hoochanlon/cn_stopwords/main/baidu_stopwords.txt').text.split()
                content = [line.strip() for line in t]
                stopwords.update(content)
                
                for group_id in group_enable:
                    try:
                        file_path = join(resource_path, f'chat_history/{group_id}.txt')
                        if exists(file_path):
                            text_list = await fileio.read_lines(file_path)
                            word_list = []
                            for text in text_list:
                                text = text.strip()
                                if text:
                                    jbc = list(jieba.cut(text))
                                    words = [word for word in jbc if word not in stopwords]
                                    word_list.extend(words)
                            if not word_list:
                                t = '本日你群一句正经话没有，服了'
                                await action.sendGroupText(group=group_id, text=t)
                            else:
                                word_list_str = " ".join(word_list)
                                wordcloud = WordCloud(
                                    background_color="white",# 设置背景颜色
                                    max_words=2000, # 词云显示的最大词数
                                    height=400, # 图片高度
                                    width=800, # 图片宽度
                                    max_font_size=50, #最大字体     
                                    stopwords=stopwords, # 设置停用词
                                    font_path=join(resource_path, 'msyh.ttc'), # 兼容中文字体，不然中文会显示乱码
                                ).generate(word_list_str)
                                img_path = join(resource_path, f'group_wordcloud/{group_id}.png')
                                wordcloud.to_file(img_path)
                                t = f"[测试版]今日词云已送达\n今日你群共聊了{len(text_list)}句话"
                                await action.sendGroupPic(group=group_id, text=t, base64=file_to_base64(img_path))
                            await fileio.clear_file(file_path)
                    except Exception as e:
                        print(e, traceback.format_exc())
                        t = f'twitter tl scheduler error\group_id: {group_id}\ntraceback: {traceback.format_exc()}'
                        await action.sendGroupText(group=1014696092, text=t)
                
                crontab_next = crontab.get_next(datetime)
mark_recv(gen_wordcloud)

async def log_chat():
    global group_enable
    if msg := ctx.__getattribute__:
        if msg.from_group in group_enable:
            msg_text = msg.text + '\n'
            await fileio.addline(join(resource_path, f'chat_history/{msg.from_group}.txt'), msg_text)
mark_recv(log_chat)
            