#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词云测试脚本
用于快速预览不同配色方案的效果
"""

import random
from os.path import join
import numpy as np
from wordcloud import WordCloud
from PIL import Image

# 模拟原插件中的配色函数
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


# 示例文本（可以替换为你自己的测试文本）
sample_text = """
聊天 开心 快乐 哈哈哈 真的 确实 太好了 厉害 牛逼 666 
加油 努力 学习 工作 生活 美好 幸福 朋友 家人 爱
游戏 好玩 有趣 精彩 赞 棒 优秀 完美 nice cool
吃饭 美食 好吃 美味 香 火锅 烧烤 奶茶 咖啡 甜点
周末 假期 旅游 玩耍 休息 放松 电影 音乐 唱歌 跳舞
天气 晴天 下雨 冷 热 温暖 舒服 凉快 
搞笑 好笑 笑死 哈哈 嘿嘿 嘻嘻 呵呵
惊讶 震惊 卧槽 我去 天哪 哇塞 
表情 可爱 萌 帅 美 漂亮 好看
点赞 转发 评论 关注 收藏 喜欢 爱了
早安 晚安 午安 你好 再见 拜拜
谢谢 感谢 辛苦了 加油 fighting
""" * 10  # 重复10次以增加词频差异

def generate_test_wordcloud(scheme_name, output_path):
    """生成测试词云"""
    print(f"正在生成 {scheme_name} 配色方案的词云...")
    
    color_func = get_gradient_color_func(scheme_name)
    
    # 使用优化后的参数
    wordcloud_data = dict(
        background_color="white",
        max_words=3000,
        height=1080,
        width=1920,
        min_font_size=10,
        max_font_size=150,
        color_func=color_func,
        collocations=False,
        font_path='resources/wordcloud/HarmonyOS.ttf',  # 确保字体路径正确
        relative_scaling=0.5,
        prefer_horizontal=0.7,
        margin=2,
        random_state=42,  # 固定随机种子以便对比
    )
    
    try:
        wordcloud = WordCloud(**wordcloud_data).generate(sample_text)
        wordcloud.to_file(output_path)
        print(f"✓ 成功生成: {output_path}")
        return True
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False


def generate_test_wordcloud_with_mask(output_path):
    """使用荔枝新年mask生成测试词云"""
    print(f"正在生成带荔枝新年mask的词云...")
    
    # 加载mask
    mask_path = 'resources/wordcloud/masks/litchi_newyear.png'
    if not exists(mask_path):
        print(f"✗ Mask文件不存在: {mask_path}")
        return False
    
    try:
        from wordcloud import ImageColorGenerator
        mask_image = Image.open(mask_path)
        mask = np.array(mask_image)
        colors = ImageColorGenerator(mask)
        
        # 使用mask时的优化配置
        wordcloud_data = dict(
            background_color="white",
            max_words=5000,
            width=2000,
            height=2000,
            min_font_size=15,
            max_font_size=200,
            mask=mask,
            color_func=colors,
            collocations=False,
            font_path='resources/wordcloud/HarmonyOS.ttf',
            relative_scaling=0.4,
            prefer_horizontal=0.75,
            margin=1,
            contour_width=2,
            contour_color='#FF6B6B',
            random_state=42,
        )
        
        wordcloud = WordCloud(**wordcloud_data).generate(sample_text)
        wordcloud.to_file(output_path)
        print(f"✓ 成功生成: {output_path}")
        return True
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数：生成所有配色方案的预览"""
    print("=" * 60)
    print("词云配色方案测试工具")
    print("=" * 60)
    
    output_dir = 'resources/wordcloud/test_output'
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # 首先生成使用mask的版本
    print("\n>>> 测试 1: 使用荔枝新年mask生成词云")
    print("-" * 60)
    mask_output = f"{output_dir}/wordcloud_litchi_newyear_mask.png"
    generate_test_wordcloud_with_mask(mask_output)
    
    # 生成不使用mask的渐变色版本作为对比
    print("\n>>> 测试 2: 生成渐变色方案词云（无mask）")
    print("-" * 60)
    schemes = ['sunset', 'ocean', 'forest', 'purple_dream', 
               'warm', 'cool', 'aurora', 'candy']
    
    success_count = 0
    for scheme in schemes:
        output_path = f"{output_dir}/wordcloud_{scheme}.png"
        if generate_test_wordcloud(scheme, output_path):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"完成! 成功生成:")
    print(f"  - 荔枝新年mask词云: 1个")
    print(f"  - 渐变色方案词云: {success_count}/{len(schemes)} 个")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 生成一个随机配色的示例
    print("\n>>> 测试 3: 随机配色方案")
    print("-" * 60)
    random_scheme = random.choice(schemes)
    output_path = f"{output_dir}/wordcloud_random_{random_scheme}.png"
    generate_test_wordcloud(random_scheme, output_path)
    print(f"随机选择的配色方案: {random_scheme}")


if __name__ == "__main__":
    from os.path import exists
    main()
