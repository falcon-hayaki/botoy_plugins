import asyncio
import copy
import json
import requests
import traceback
import re
import random
from os.path import join, exists, isfile
from os import system, listdir
import os, time
from datetime import datetime, timezone
import jieba
import numpy as np
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from PIL import Image
from botoy import mark_recv, ctx, action, file_to_base64, jconfig, async_run, to_async
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

resource_path = 'resources/wordcloud'
from utils.tz import beijingnow
from utils import fileio

system(f"mkdir -p {join(resource_path, 'chat_history')}")
system(f"mkdir -p {join(resource_path, 'group_wordcloud')}")

# 使用 APScheduler 进行定时任务调度
scheduler = AsyncIOScheduler()

with open(join(resource_path, 'group_enable.json'), 'r') as f:
    group_enable = json.load(f)

# 定义多种现代化的渐变色彩方案
def get_gradient_color_func(color_scheme='default'):
    """
    返回一个颜色函数，用于词云的渐变配色
    支持多种流行的配色方案
    """
    color_schemes = {
        'sunset': [  # 日落霞光
            '#FF6B6B', '#FFE66D', '#FF8E53', '#FE4A49', '#F9844A'
        ],
        'ocean': [  # 海洋渐变
            '#00D4FF', '#0099CC', '#0066CC', '#003D99', '#5DADE2'
        ],
        'forest': [  # 森林绿意
            '#2ECC71', '#27AE60', '#1ABC9C', '#16A085', '#52BE80'
        ],
        'purple_dream': [  # 紫色梦幻
            '#9B59B6', '#8E44AD', '#AF7AC5', '#D2B4DE', '#BB8FCE'
        ],
        'warm': [  # 温暖橙红
            '#E74C3C', '#EC7063', '#F39C12', '#F8B739', '#E67E22'
        ],
        'cool': [  # 冷色调
            '#3498DB', '#5DADE2', '#85C1E9', '#AED6F1', '#2980B9'
        ],
        'aurora': [  # 极光色
            '#A29BFE', '#6C5CE7', '#FD79A8', '#FDCB6E', '#00B894'
        ],
        'candy': [  # 糖果色
            '#FF6B9D', '#FFC93C', '#C3BEF7', '#A1EAFB', '#FFB6B9'
        ]
    }
    
    colors = color_schemes.get(color_scheme, color_schemes['sunset'])
    
    def color_func(word=None, font_size=None, position=None, orientation=None, font_path=None, random_state=None):
        # 根据字体大小选择颜色，大的词用更鲜艳的颜色
        if font_size:
            # 归一化字体大小
            idx = min(int((font_size / 100) * len(colors)), len(colors) - 1)
        else:
            idx = random.randint(0, len(colors) - 1)
        return colors[idx]
    
    return color_func

@to_async
def gen_wordcloud(word_list_str: str, wordcloud_data: dict, img_path: str):
    wordcloud = WordCloud(**wordcloud_data).generate(word_list_str)
    wordcloud.to_file(img_path)

# 不使用异步
def gen_wordcloud_sync(word_list_str: str, wordcloud_data: dict, img_path: str):
    wordcloud = WordCloud(**wordcloud_data).generate(word_list_str)
    wordcloud.to_file(img_path)
    
async def gen_wordcloud_task():
    """定时生成词云任务 - 由 APScheduler 调度"""
    global group_enable
    # 停用词
    stopwords = set()
    t = requests.get('https://raw.githubusercontent.com/hoochanlon/cn_stopwords/main/baidu_stopwords.txt').text.split()
    content = [line.strip() for line in t]
    stopwords.update(content)
    
    # 使用固定的 litchi_newyear mask
    mask = None
    colors = None
    mask_path = join(resource_path, 'masks/litchi_newyear.png')
    if exists(mask_path):
        mask_image = Image.open(mask_path)
        mask = np.array(mask_image)
        colors = ImageColorGenerator(mask)
    
    # jieba.enable_paddle()
    for group_id in group_enable:
        # if group_id != 723979982:
        #     continue
        try:
            file_path = join(resource_path, f'chat_history/{group_id}.txt')
            lock_path = join(resource_path, f'chat_history/{group_id}.lock')
            STALE_SECONDS = 60 * 60 * 2  # 2 hours

            # 尝试创建原子 lock 文件，若已存在则跳过；若 lock 过旧则清理后重试
            lock_created = False
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                lock_created = True
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(lock_path) > STALE_SECONDS:
                        os.remove(lock_path)
                        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                        os.close(fd)
                        lock_created = True
                except Exception:
                    lock_created = False

            if not lock_created:
                # 其他进程/协程正在处理；跳过以避免重复生成
                continue

            try:
                text_list = []
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
                    
                    # 使用mask时的优化配置
                    if mask is not None:
                        # 使用 mask 时的参数配置
                        wordcloud_data = dict(
                            background_color="white",  # 白色背景更适合展示mask形状
                            max_words=5000,  # 使用mask时可以放更多词
                            width=2000,  # 根据mask调整尺寸
                            height=2000,
                            min_font_size=15,  # 稍大的最小字体，确保清晰
                            max_font_size=200,  # 更大的字体以填充mask形状
                            stopwords=stopwords,
                            mask=mask,  # 使用mask
                            color_func=colors,  # 从mask图片提取颜色
                            collocations=False,
                            font_path=join(resource_path, 'HarmonyOS.ttf'),
                            relative_scaling=0.4,  # 降低相对缩放，让词语大小分布更均匀
                            prefer_horizontal=0.75,  # 更多水平词语，更易读
                            margin=1,  # 更紧密的间距以填充mask
                            contour_width=2,  # 添加轮廓线宽度
                            contour_color='#FF6B6B',  # 轮廓颜色（可选，可以注释掉）
                            random_state=None,
                        )
                        scheme_info = "荔枝新年主题 (Litchi New Year)"
                    else:
                        # 没有mask时使用渐变色方案
                        color_schemes_list = ['sunset', 'ocean', 'forest', 'purple_dream', 
                                             'warm', 'cool', 'aurora', 'candy']
                        chosen_scheme = random.choice(color_schemes_list)
                        color_func = get_gradient_color_func(chosen_scheme)
                        
                        wordcloud_data = dict(
                            background_color="white",
                            max_words=3000,
                            height=1080,
                            width=1920,
                            min_font_size=10,
                            max_font_size=150,
                            stopwords=stopwords,
                            color_func=color_func,
                            collocations=False,
                            font_path=join(resource_path, 'HarmonyOS.ttf'),
                            relative_scaling=0.5,
                            prefer_horizontal=0.7,
                            margin=2,
                            random_state=None,
                        )
                        scheme_info = chosen_scheme
                    
                    img_path = join(resource_path, f'group_wordcloud/{group_id}.png')
                    
                    gen_wordcloud_sync(word_list_str, wordcloud_data, img_path)
                    # await gen_wordcloud(word_list_str, wordcloud_data, img_path)
                    # await async_run(gen_wordcloud_sync, word_list_str, wordcloud_data, img_path)
                    
                    t = f"📊 今日词云已送达\n今日你群共聊了{len(text_list)}句话"
                    await action.sendGroupPic(group=group_id, text=t, base64=file_to_base64(img_path))
                
                # 清空文件（如果存在）
                if exists(file_path):
                    await fileio.clear_file(file_path)
                
                await asyncio.sleep(10)
            finally:
                try:
                    if os.path.exists(lock_path):
                        os.remove(lock_path)
                except Exception:
                    pass
        except Exception as e:
            logger.exception(f'wordcloud scheduler error group_id: {group_id}')
            t = f'wordcloud scheduler error\ngroup_id: {group_id}\ntraceback: {traceback.format_exc()}'
            await action.sendGroupText(group=1014696092, text=t)


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


# 配置 APScheduler 定时任务

# ========== 测试任务：每分钟执行 ==========
# scheduler.add_job(
#     gen_wordcloud_task,
#     CronTrigger(minute='*'),  # 每分钟执行
#     id='wordcloud_test',
#     name='词云测试(每分钟)',
#     replace_existing=True
# )

# ========== 生产任务：每天 00:15 执行 ==========
scheduler.add_job(
    gen_wordcloud_task,
    CronTrigger(hour=0, minute=15),  # 每天 00:15
    id='wordcloud_daily',
    name='每日词云生成',
    replace_existing=True
)

# 延迟启动 scheduler，直到事件循环运行
_scheduler_started = False

async def start_scheduler():
    """在事件循环运行后启动 scheduler"""
    global _scheduler_started
    if not _scheduler_started:
        scheduler.start()
        _scheduler_started = True
        logger.info("词云定时任务已配置")

mark_recv(start_scheduler)
