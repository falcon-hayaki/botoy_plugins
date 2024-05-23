import asyncio
import copy
import json
import requests
import traceback
import re
import random
from os.path import join, exists, isfile
from os import system, listdir
from croniter import croniter
from datetime import datetime, timezone
import jieba
import numpy as np
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
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
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                # 停用词
                stopwords = set()
                t = requests.get('https://raw.githubusercontent.com/hoochanlon/cn_stopwords/main/baidu_stopwords.txt').text.split()
                content = [line.strip() for line in t]
                stopwords.update(content)
                # 随机选取mask
                mask = None
                colors = None
                files = [f for f in listdir(join(resource_path, 'masks/')) if isfile(join(resource_path, f'masks/{f}'))]
                if files:
                    mask = np.array(Image.open(join(resource_path, f'masks/{random.choice(files)}')))
                    colors = ImageColorGenerator(mask)
                
                for group_id in group_enable:
                    # if group_id != 723979982:
                    #     continue
                    try:
                        file_path = join(resource_path, f'chat_history/{group_id}.txt')
                        if exists(file_path):
                            text_list = await fileio.read_lines(file_path)
                            word_list = []
                            for text in text_list:
                                text = text.strip()
                                if text:
                                    # 分词
                                    # jieba.enable_paddle():
                                    # jbc = list(jieba.cut(text, use_paddle=True))
                                    # words = [word for word in jbc if word not in stopwords]
                                    # word_list.extend(words)
                                    # 不分词
                                    word_list.append(text)
                            if not word_list:
                                t = '本日你群一句正经话没有，服了'
                                await action.sendGroupText(group=group_id, text=t)
                            else:
                                word_list_str = " ".join(word_list)
                                wordcloud = WordCloud(
                                    background_color="white",
                                    max_words=2000,
                                    height=400,
                                    width=800,
                                    max_font_size=233,
                                    stopwords=stopwords,
                                    mask=mask,
                                    color_func=colors,
                                    collocations=False,
                                    font_path=join(resource_path, 'HarmonyOS.ttf'),
                                ).generate(word_list_str)
                                img_path = join(resource_path, f'group_wordcloud/{group_id}.png')
                                wordcloud.to_file(img_path)
                                t = f"[测试版]今日词云已送达\n今日你群共聊了{len(text_list)}句话"
                                await action.sendGroupPic(group=group_id, text=t, base64=file_to_base64(img_path))
                            await fileio.clear_file(file_path)
                            await asyncio.sleep(10)
                    except Exception as e:
                        print(e, traceback.format_exc())
                        t = f'twitter tl scheduler error\group_id: {group_id}\ntraceback: {traceback.format_exc()}'
                        await action.sendGroupText(group=1014696092, text=t)
                
                crontab_next = crontab.get_next(datetime)
mark_recv(gen_wordcloud)

def remove_abstract_content(text:str):
    if text.startswith('{') and text.endswith('}'):
        return ''
    if text.startswith('<') and text.endswith('>'):
        return ''
    # 排除链接
    link_pattern = re.compile(r'https?://\S+|www\.\S+')
    text = link_pattern.sub('', text)
    # 排除@ 
    # NOTE: 由于@的名字中若出现空格将无法完整剔除，
    #       于是将包含@的整句话直接排除掉
    # mention_pattern = re.compile(r'@\S+\s?')
    # text = mention_pattern.sub('', text)
    if '@' in text:
        return ''
    return text
async def log_chat():
    global group_enable
    if msg := ctx.g:
        if msg.from_user != jconfig.qq and msg.from_group in group_enable:
            msg_text = remove_abstract_content(msg.text)
            if msg_text:
                msg_text = msg_text + '\n'
                await fileio.addline(join(resource_path, f'chat_history/{msg.from_group}.txt'), msg_text)
mark_recv(log_chat)
            