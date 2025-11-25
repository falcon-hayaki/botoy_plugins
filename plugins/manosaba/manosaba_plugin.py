"""
Manosaba Plugin - 魔法少女贴图生成器
无需外部依赖的图片生成脚本，提供纯函数接口
"""

import os
import random
import io
import time
import urllib.request
from io import BytesIO
from typing import Tuple, Union, Literal, Optional
from PIL import Image, ImageDraw, ImageFont
from urllib.error import URLError, HTTPError

from .main import resource_path

# ==================== 全局配置 ====================

# 图片压缩设置
IMAGE_SETTINGS = {
    "max_width": 1200,
    "max_height": 800,
    "quality": 65,
    "resize_ratio": 0.7
}

# 角色配置字典
MAHOSHOJO = {
    "ema": {"emotion_count": 8, "font": "font3.ttf"},       # 樱羽艾玛
    "hiro": {"emotion_count": 6, "font": "font3.ttf"},      # 二阶堂希罗
    "sherri": {"emotion_count": 7, "font": "font3.ttf"},    # 橘雪莉
    "hanna": {"emotion_count": 5, "font": "font3.ttf"},     # 远野汉娜
    "anan": {"emotion_count": 9, "font": "font3.ttf"},      # 夏目安安
    "yuki": {"emotion_count": 18, "font": "font3.ttf"},     # 月代雪
    "meruru": {"emotion_count": 6, "font": "font3.ttf"},    # 冰上梅露露
    "noa": {"emotion_count": 6, "font": "font3.ttf"},       # 城崎诺亚
    "reia": {"emotion_count": 7, "font": "font3.ttf"},      # 莲见蕾雅
    "miria": {"emotion_count": 4, "font": "font3.ttf"},     # 佐伯米莉亚
    "nanoka": {"emotion_count": 5, "font": "font3.ttf"},    # 黑部奈叶香
    "mago": {"emotion_count": 5, "font": "font3.ttf"},      # 宝生玛格
    "alisa": {"emotion_count": 6, "font": "font3.ttf"},     # 紫藤亚里沙
    "coco": {"emotion_count": 5, "font": "font3.ttf"}       # 泽渡可可
}

# 角色昵称映射
NICKNAME_MAP = {
    # 樱羽艾玛
    "ema": ["ema", "艾玛"],
    # 二阶堂希罗
    "hiro": ["hiro", "希罗"],
    # 橘雪莉
    "sherri": ["sherri", "雪莉", "猩猩", "大猩猩", "星街彗星", "星姐", "丰川祥子", "祥子", "怪力女"],
    # 远野汉娜
    "hanna": ["hanna", "汉娜"],
    # 夏目安安
    "anan": ["anan", "安安"],
    # 月代雪
    "yuki": ["yuki", "雪", "大魔女"],
    # 冰上梅露露
    "meruru": ["meruru", "梅露露"],
    # 城崎诺亚
    "noa": ["noa", "诺亚"],
    # 莲见蕾雅
    "reia": ["reia", "蕾雅"],
    # 佐伯米莉亚
    "miria": ["miria", "米莉亚"],
    # 黑部奈叶香
    "nanoka": ["nanoka", "奈叶香"],
    # 宝生玛格
    "mago": ["mago", "玛格"],
    # 紫藤亚里沙
    "alisa": ["alisa", "亚里沙"],
    # 泽渡可可
    "coco": ["coco", "可可"]
}

# 角色文字配置字典
TEXT_CONFIGS_DICT = {
    "nanoka": [  # 黑部奈叶香
        {"text": "黑", "position": (759, 63), "font_color": (131, 143, 147), "font_size": 196},
        {"text": "部", "position": (955, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "奈", "position": (1053, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "叶香", "position": (1197, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "hiro": [  # 二阶堂希罗
        {"text": "二", "position": (759, 63), "font_color": (239, 79, 84), "font_size": 196},
        {"text": "阶堂", "position": (955, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "希", "position": (1143, 110), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "罗", "position": (1283, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "ema": [  # 樱羽艾玛
        {"text": "樱", "position": (759, 73), "font_color": (253, 145, 175), "font_size": 186},
        {"text": "羽", "position": (949, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "艾", "position": (1039, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "玛", "position": (1183, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "sherri": [  # 橘雪莉
        {"text": "橘", "position": (759, 73), "font_color": (137, 177, 251), "font_size": 186},
        {"text": "雪", "position": (943, 110), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "莉", "position": (1093, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "", "position": (0, 0), "font_color": (255, 255, 255), "font_size": 1}
    ],
    "anan": [  # 夏目安安
        {"text": "夏", "position": (759, 73), "font_color": (159, 145, 251), "font_size": 186},
        {"text": "目", "position": (949, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "安", "position": (1039, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "安", "position": (1183, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "noa": [  # 城崎诺亚
        {"text": "城", "position": (759, 73), "font_color": (104, 223, 231), "font_size": 186},
        {"text": "崎", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "诺", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "亚", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "coco": [  # 泽渡可可
        {"text": "泽", "position": (759, 73), "font_color": (251, 114, 78), "font_size": 186},
        {"text": "渡", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "可", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "可", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "alisa": [  # 紫藤亚里沙
        {"text": "紫", "position": (759, 73), "font_color": (235, 75, 60), "font_size": 186},
        {"text": "藤", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "亚", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "里沙", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "reia": [  # 莲见蕾雅
        {"text": "莲", "position": (759, 73), "font_color": (253, 177, 88), "font_size": 186},
        {"text": "见", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "蕾", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "雅", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "mago": [  # 宝生玛格
        {"text": "宝", "position": (759, 73), "font_color": (185, 124, 235), "font_size": 186},
        {"text": "生", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "玛", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "格", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "hanna": [  # 远野汉娜
        {"text": "远", "position": (759, 73), "font_color": (169, 199, 30), "font_size": 186},
        {"text": "野", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "汉", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "娜", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "meruru": [  # 冰上梅露露
        {"text": "冰", "position": (759, 73), "font_color": (227, 185, 175), "font_size": 186},
        {"text": "上", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "梅", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "露露", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "miria": [  # 佐伯米莉亚
        {"text": "佐", "position": (759, 73), "font_color": (235, 207, 139), "font_size": 186},
        {"text": "伯", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "米", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "莉亚", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "yuki": [  # 月代雪
        {"text": "月", "position": (759, 63), "font_color": (195, 209, 231), "font_size": 196},
        {"text": "代", "position": (948, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "雪", "position": (1053, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "", "position": (0, 0), "font_color": (255, 255, 255), "font_size": 1}
    ]
}

# 文本框配置
TEXT_BOX_CONFIG = {
    "top_left": (728, 355),      # 文本范围起始位置
    "bottom_right": (2339, 800)  # 文本范围右下角位置
}

# 类型定义
Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

# ==================== Emoji 处理 ====================

ZWJ = 0x200D
VS16 = 0xFE0F
TWEMOJI_BASE = "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/"


def is_regional_indicator(cp: int) -> bool:
    return 0x1F1E6 <= cp <= 0x1F1FF


def is_skin_tone(cp: int) -> bool:
    return 0x1F3FB <= cp <= 0x1F3FF


def is_emoji_base(cp: int) -> bool:
    return (
        0x1F000 <= cp <= 0x1FAFF or
        0x2600 <= cp <= 0x27BF or
        0x2300 <= cp <= 0x23FF or
        0x2B00 <= cp <= 0x2BFF
    )


def is_emoji_char(ch: str) -> bool:
    cp = ord(ch)
    return is_emoji_base(cp) or cp in (ZWJ, VS16) or is_skin_tone(cp) or is_regional_indicator(cp)


def iter_emoji_clusters(s: str):
    """拆分字符串为 emoji cluster"""
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        cp = ord(ch)

        if not is_emoji_base(cp):
            yield ch, False
            i += 1
            continue

        cluster = ch
        i += 1

        while i < n:
            nxt = s[i]
            ncp = ord(nxt)

            if ncp == VS16 or is_skin_tone(ncp):
                cluster += nxt
                i += 1
                continue

            if ncp == ZWJ:
                if i + 1 < n:
                    cluster += nxt + s[i + 1]
                    i += 2
                    continue
                else:
                    cluster += nxt
                    i += 1
                    continue

            if is_regional_indicator(ncp) and is_regional_indicator(ord(cluster[-1])):
                cluster += nxt
                i += 1
                continue

            break

        yield cluster, True


def emoji_cluster_to_filename(cluster: str) -> str:
    """Emoji cluster 转换为文件名"""
    cps = []
    for ch in cluster:
        cp = ord(ch)
        if cp == VS16:
            continue
        cps.append(cp)
    return "-".join(f"{cp:x}" for cp in cps) + ".png"


def download_emoji_png(
    url: str,
    save_path: str,
    timeout: float = 6.0,
    retries: int = 2,
    backoff: float = 0.25
) -> Optional[Image.Image]:
    """从网络下载 emoji PNG"""
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (emoji-downloader)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()

            im = Image.open(BytesIO(data)).convert("RGBA")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            im.save(save_path, format="PNG")
            return im

        except (HTTPError, URLError, OSError, ValueError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))

    return None


# ==================== 图片处理工具函数 ====================

def compress_image(image: Image.Image) -> Image.Image:
    """压缩图像大小"""
    width, height = image.size
    new_width = int(width * IMAGE_SETTINGS["resize_ratio"])
    new_height = int(height * IMAGE_SETTINGS["resize_ratio"])

    if new_width > IMAGE_SETTINGS["max_width"]:
        ratio = IMAGE_SETTINGS["max_width"] / new_width
        new_width, new_height = IMAGE_SETTINGS["max_width"], int(new_height * ratio)

    if new_height > IMAGE_SETTINGS["max_height"]:
        ratio = IMAGE_SETTINGS["max_height"] / new_height
        new_height, new_width = IMAGE_SETTINGS["max_height"], int(new_width * ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def get_font_path(font_name: str, script_dir: str) -> str:
    """获取字体文件的绝对路径"""
    font_path = os.path.join(script_dir, "fonts", font_name)
    if os.path.exists(font_path):
        return font_path
    return font_name


def load_font(size: int, font_path: str = None) -> ImageFont.FreeTypeFont:
    """加载字体"""
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size=size)
        except:
            pass
    
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except:
        return ImageFont.load_default()


# ==================== 绘制文本函数 ====================

def draw_text_auto(
    image_source: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    text: str,
    color: Tuple[int, int, int] = (0, 0, 0),
    max_font_height: int = None,
    font_path: str = None,
    align: Align = "center",
    valign: VAlign = "middle",
    line_spacing: float = 0.15,
    bracket_color: Tuple[int, int, int] = (137, 177, 251),
    image_overlay: Union[str, Image.Image, None] = None,
    role_name: str = "unknown",
    text_configs_dict: dict = None,
    emoji_enabled: bool = True,
    emoji_download_retries: int = 2,
    emoji_image_dir: str = None,
    emoji_scale: float = 1.0,
    emoji_download_timeout: float = 6.0,
    base_dir: str = None
) -> bytes:
    """
    在指定矩形内自适应字号绘制文本
    """

    if isinstance(image_source, Image.Image):
        img = image_source.copy()
    else:
        img = Image.open(image_source).convert("RGBA")

    draw = ImageDraw.Draw(img)

    if image_overlay is not None:
        if isinstance(image_overlay, Image.Image):
            img_overlay = image_overlay.copy()
        else:
            img_overlay = Image.open(image_overlay).convert("RGBA") if os.path.isfile(image_overlay) else None

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的文字区域。")
    region_w, region_h = x2 - x1, y2 - y1

    if emoji_image_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        emoji_image_dir = os.path.join(script_dir, "emoji_png")

    emoji_cache: dict[str, Image.Image] = {}

    def _load_emoji_png(cluster: str) -> Optional[Image.Image]:
        if not emoji_enabled:
            return None

        fn = emoji_cluster_to_filename(cluster)
        path = os.path.join(emoji_image_dir, fn)

        if path in emoji_cache:
            return emoji_cache[path]

        if os.path.exists(path):
            try:
                im = Image.open(path).convert("RGBA")
                emoji_cache[path] = im
                return im
            except:
                try:
                    os.remove(path)
                except:
                    pass

        url = TWEMOJI_BASE + fn
        im = download_emoji_png(
            url,
            path,
            timeout=emoji_download_timeout,
            retries=max(0, int(emoji_download_retries))
        )
        if im is not None:
            emoji_cache[path] = im
            return im

        return None

    def emoji_advance_px(font_main: ImageFont.FreeTypeFont) -> int:
        ascent, descent = font_main.getmetrics()
        line_px = ascent + descent
        return max(1, int(line_px * emoji_scale))

    def text_width(txt: str, font_main: ImageFont.FreeTypeFont) -> float:
        if not emoji_enabled:
            return draw.textlength(txt, font=font_main)

        w = 0.0
        em_px = emoji_advance_px(font_main)
        for cluster, is_em in iter_emoji_clusters(txt):
            if is_em:
                w += em_px
            else:
                w += draw.textlength(cluster, font=font_main)
        return w

    def wrap_lines(txt: str, font_main: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        lines: list[str] = []
        for para in txt.splitlines() or [""]:
            has_space = (" " in para)
            units = para.split(" ") if has_space else list(para)
            buf = ""

            def unit_join(a: str, b: str) -> str:
                if not a:
                    return b
                return (a + " " + b) if has_space else (a + b)

            for u in units:
                trial = unit_join(buf, u)
                w = text_width(trial, font_main)
                if w <= max_w:
                    buf = trial
                else:
                    if buf:
                        lines.append(buf)

                    if has_space and len(u) > 1:
                        tmp = ""
                        for ch in u:
                            if text_width(tmp + ch, font_main) <= max_w:
                                tmp += ch
                            else:
                                if tmp:
                                    lines.append(tmp)
                                tmp = ch
                        buf = tmp
                    else:
                        if text_width(u, font_main) <= max_w:
                            buf = u
                        else:
                            lines.append(u)
                            buf = ""
            if buf != "":
                lines.append(buf)
            if para == "" and (not lines or lines[-1] != ""):
                lines.append("")
        return lines

    def measure_block(lines: list[str], font_main: ImageFont.FreeTypeFont):
        ascent, descent = font_main.getmetrics()
        line_h = int((ascent + descent) * (1 + line_spacing))
        max_w = 0
        for ln in lines:
            max_w = max(max_w, int(text_width(ln, font_main)))
        total_h = max(line_h * max(1, len(lines)), 1)
        return max_w, total_h, line_h

    # 二分最大字号
    hi = min(region_h, max_font_height) if max_font_height else region_h
    lo, best_size, best_lines, best_line_h, best_block_h = 1, 0, [], 0, 0

    while lo <= hi:
        mid = (lo + hi) // 2
        font_main = load_font(mid, font_path)
        lines = wrap_lines(text, font_main, region_w)
        w, h, lh = measure_block(lines, font_main)
        if w <= region_w and h <= region_h:
            best_size, best_lines, best_line_h, best_block_h = mid, lines, lh, h
            lo = mid + 1
        else:
            hi = mid - 1

    if best_size == 0:
        font_main = load_font(1, font_path)
        best_lines = wrap_lines(text, font_main, region_w)
        best_line_h, best_block_h = 1, 1
        best_size = 1
    else:
        font_main = load_font(best_size, font_path)

    em_px = emoji_advance_px(font_main)
    ascent, descent = font_main.getmetrics()

    # 解析中括号着色
    def parse_color_segments(s: str, in_bracket: bool):
        segs = []
        buf = ""
        for ch in s:
            if ch in ("[", "【"):
                if buf:
                    segs.append((buf, bracket_color if in_bracket else color))
                    buf = ""
                segs.append((ch, bracket_color))
                in_bracket = True
            elif ch in ("]", "】"):
                if buf:
                    segs.append((buf, bracket_color))
                    buf = ""
                segs.append((ch, bracket_color))
                in_bracket = False
            else:
                buf += ch
        if buf:
            segs.append((buf, bracket_color if in_bracket else color))
        return segs, in_bracket

    # 垂直对齐
    if valign == "top":
        y_start = y1
    elif valign == "middle":
        y_start = y1 + (region_h - best_block_h) // 2
    else:
        y_start = y2 - best_block_h

    # 绘制文本
    y = y_start
    in_bracket = False
    shadow_offset = (4, 4)

    for ln in best_lines:
        line_w = int(text_width(ln, font_main))

        if align == "left":
            x = x1
        elif align == "center":
            x = x1 + (region_w - line_w) // 2
        else:
            x = x2 - line_w

        segments, in_bracket = parse_color_segments(ln, in_bracket)

        for seg_text, seg_color in segments:
            if not emoji_enabled:
                draw.text((x + shadow_offset[0], y + shadow_offset[1]),
                          seg_text, font=font_main, fill=(0, 0, 0))
                draw.text((x, y), seg_text, font=font_main, fill=seg_color)
                x += int(draw.textlength(seg_text, font=font_main))
                continue

            for cluster, is_em in iter_emoji_clusters(seg_text):
                if is_em:
                    em_img = _load_emoji_png(cluster)
                    if em_img is None:
                        draw.text((x, y), "□", font=font_main, fill=seg_color)
                        x += int(draw.textlength("□", font=font_main))
                        continue

                    em_draw = em_img.resize((em_px, em_px), Image.Resampling.LANCZOS)
                    em_y = y + ascent - em_px

                    img.paste(em_draw, (x + shadow_offset[0], em_y + shadow_offset[1]), em_draw)
                    img.paste(em_draw, (x, em_y), em_draw)

                    x += em_px
                else:
                    draw.text((x + shadow_offset[0], y + shadow_offset[1]),
                              cluster, font=font_main, fill=(0, 0, 0))
                    draw.text((x, y), cluster, font=font_main, fill=seg_color)
                    x += int(draw.textlength(cluster, font=font_main))

        y += best_line_h
        if y - y_start > region_h:
            break

    # 覆盖置顶图层
    if image_overlay is not None and img_overlay is not None:
        img.paste(img_overlay, (0, 0), img_overlay)

    # 角色专属文字
    if text_configs_dict and role_name in text_configs_dict:
        shadow_offset2 = (2, 2)
        shadow_color2 = (0, 0, 0)
        
        for config in text_configs_dict[role_name]:
            t = config["text"]
            position = config["position"]
            font_color = config["font_color"]
            font_size = config["font_size"]

            if base_dir:
                font_path2 = os.path.join(base_dir, "fonts", "font3.ttf")
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                font_path2 = os.path.join(script_dir, "font3.ttf")

            try:
                font2 = ImageFont.truetype(font_path2, font_size)
            except:
                font2 = load_font(font_size)

            shadow_position = (position[0] + shadow_offset2[0], position[1] + shadow_offset2[1])
            draw.text(shadow_position, t, fill=shadow_color2, font=font2)
            draw.text(position, t, fill=font_color, font=font2)

    img = compress_image(img)

    buf = BytesIO()
    img.save(buf, "png")
    return buf.getvalue()


# ==================== 粘贴图片函数 ====================

def paste_image_auto(
    image_source: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    content_image: Image.Image,
    align: Align = "center",
    valign: VAlign = "middle",
    padding: int = 0,
    allow_upscale: bool = False,
    keep_alpha: bool = True,
    image_overlay: Union[str, Image.Image, None] = None,
    max_image_size: Tuple[int, int] = (None, None),
    role_name: str = "unknown",
    text_configs_dict: dict = None,
    base_dir: str = None,
) -> bytes:
    """
    在指定矩形内放置一张图片
    """
    if not isinstance(content_image, Image.Image):
        raise TypeError("content_image 必须为 PIL.Image.Image")

    if isinstance(image_source, Image.Image):
        img = image_source.copy()
    else:
        img = Image.open(image_source).convert("RGBA")

    if image_overlay is not None:
        if isinstance(image_overlay, Image.Image):
            img_overlay = image_overlay.copy()
        else:
            img_overlay = Image.open(image_overlay).convert("RGBA") if os.path.isfile(image_overlay) else None

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的粘贴区域。")

    region_w = max(1, (x2 - x1) - 2 * padding)
    region_h = max(1, (y2 - y1) - 2 * padding)

    cw, ch = content_image.size
    if cw <= 0 or ch <= 0:
        raise ValueError("content_image 尺寸无效。")

    scale_w = region_w / cw
    scale_h = region_h / ch
    scale = min(scale_w, scale_h)

    if not allow_upscale:
        scale = min(1.0, scale)

    max_width, max_height = max_image_size
    if max_width is not None:
        scale_w_limit = max_width / cw
        scale = min(scale, scale_w_limit)
    if max_height is not None:
        scale_h_limit = max_height / ch
        scale = min(scale, scale_h_limit)

    new_w = max(1, int(round(cw * scale)))
    new_h = max(1, int(round(ch * scale)))

    resized = content_image.resize((new_w, new_h), Image.LANCZOS)

    if align == "left":
        px = x1 + padding
    elif align == "center":
        px = x1 + padding + (region_w - new_w) // 2
    else:
        px = x2 - padding - new_w

    if valign == "top":
        py = y1 + padding
    elif valign == "middle":
        py = y1 + padding + (region_h - new_h) // 2
    else:
        py = y2 - padding - new_h

    if keep_alpha and ("A" in resized.getbands()):
        img.paste(resized, (px, py), resized)
    else:
        img.paste(resized, (px, py))

    if image_overlay is not None and img_overlay is not None:
        img.paste(img_overlay, (0, 0), img_overlay)

    # 角色专属文字
    if text_configs_dict and role_name in text_configs_dict:
        draw = ImageDraw.Draw(img)
        shadow_offset2 = (2, 2)
        shadow_color2 = (0, 0, 0)
        
        for config in text_configs_dict[role_name]:
            t = config["text"]
            position = config["position"]
            font_color = config["font_color"]
            font_size = config["font_size"]
            
            if base_dir:
                font_path2 = os.path.join(base_dir, "fonts", "font3.ttf")
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                font_path2 = os.path.join(script_dir, "font3.ttf")
                
            try:
                font2 = ImageFont.truetype(font_path2, font_size)
            except:
                font2 = load_font(font_size)
            
            shadow_position = (position[0] + shadow_offset2[0], position[1] + shadow_offset2[1])
            draw.text(shadow_position, t, fill=shadow_color2, font=font2)
            draw.text(position, t, fill=font_color, font=font2)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ==================== 背景与表情加载函数 ====================

def get_background_and_character_image(
    base_dir: str,
    character_name: str,
    background_index: int = 0,
    expression_index: int = 0
) -> Tuple[Image.Image, Image.Image]:
    """
    获取背景图和角色表情图
    
    Args:
        base_dir: 项目基础目录
        character_name: 角色名称 (如 "sherri")
        background_index: 背景索引 (0-15)
        expression_index: 表情索引 (0-emotion_count-1)
    
    Returns:
        (背景图, 角色表情图)
    """
    if character_name not in MAHOSHOJO:
        raise ValueError(f"角色不存在: {character_name}")
    
    emotion_count = MAHOSHOJO[character_name]["emotion_count"]
    if not (0 <= expression_index < emotion_count):
        raise ValueError(f"表情索引超出范围 (0-{emotion_count-1})")
    
    if not (0 <= background_index < 16):
        raise ValueError(f"背景索引超出范围 (0-15)")
    
    background_path = os.path.join(base_dir, "imgs", "background", f"c{background_index + 1}.png")
    character_path = os.path.join(base_dir, "imgs", "characters", character_name, f"{character_name} ({expression_index + 1}).png")
    
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"背景图不存在: {background_path}")
    if not os.path.exists(character_path):
        raise FileNotFoundError(f"角色表情图不存在: {character_path}")
    
    bg_image = Image.open(background_path).convert("RGBA")
    char_image = Image.open(character_path).convert("RGBA")
    
    return bg_image, char_image


def merge_character_to_background(
    background: Image.Image,
    character: Image.Image,
    y_offset: int = 134
) -> Image.Image:
    """
    将角色表情图合并到背景图上
    
    Args:
        background: 背景图
        character: 角色表情图
        y_offset: Y轴偏移（默认134）
    
    Returns:
        合并后的图像
    """
    result = background.copy()
    result.paste(character, (0, y_offset), character)
    return result


# ==================== 主接口函数 ====================

def generate_image_with_text(
    base_dir: str,
    character_name: str,
    text: str,
    background_index: int = 0,
    expression_index: int = 0,
    max_font_height: int = 145,
    emoji_enabled: bool = True,
    emoji_download_retries: int = 2,
) -> bytes:
    """
    生成包含文本的图片
    
    Args:
        base_dir: 项目基础目录（包含 background, character_name 等目录）
        character_name: 角色名称 (如 "sherri", "anan" 等)
        text: 要绘制的文本
        background_index: 背景索引 (0-15, 默认0)
        expression_index: 表情索引 (0-emotion_count-1, 默认0)
        max_font_height: 最大字号高度 (默认145)
        emoji_enabled: 是否启用 emoji (默认True)
        emoji_download_retries: emoji 下载重试次数 (默认2)
    
    Returns:
        PNG 图片的 bytes
    
    Example:
        >>> png_bytes = generate_image_with_text(
        ...     base_dir="C:\\path\\to\\project",
        ...     character_name="sherri",
        ...     text="你好啊！[开心]",
        ...     background_index=0,
        ...     expression_index=0
        ... )
        >>> with open("output.png", "wb") as f:
        ...     f.write(png_bytes)
    """
    # 获取背景和角色表情
    background, character = get_background_and_character_image(
        base_dir, character_name, background_index, expression_index
    )
    
    # 合并图像
    merged_image = merge_character_to_background(background, character)
    
    # 获取字体路径
    font_path = get_font_path(
        MAHOSHOJO[character_name]["font"],
        base_dir
    )
    
    # 获取高亮颜色（如果是特定角色）
    highlight_args = {}
    if character_name == "anan":
        highlight_args = {"bracket_color": (159, 145, 251)}
    
    emoji_image_dir = os.path.join(base_dir, "imgs", "emoji_png")

    # 绘制文本
    png_bytes = draw_text_auto(
        image_source=merged_image,
        image_overlay=None,
        top_left=TEXT_BOX_CONFIG["top_left"],
        bottom_right=TEXT_BOX_CONFIG["bottom_right"],
        text=text,
        align="left",
        valign="top",
        color=(255, 255, 255),
        max_font_height=max_font_height,
        font_path=font_path,
        role_name=character_name,
        text_configs_dict=TEXT_CONFIGS_DICT,
        emoji_enabled=emoji_enabled,
        emoji_download_retries=emoji_download_retries,
        emoji_image_dir=emoji_image_dir,
        base_dir=base_dir,
        **highlight_args
    )
    
    return png_bytes


def generate_image_with_picture(
    base_dir: str,
    character_name: str,
    content_image: Image.Image,
    background_index: int = 0,
    expression_index: int = 0,
    padding: int = 12,
    allow_upscale: bool = True,
) -> bytes:
    """
    生成包含图片的贴图
    
    Args:
        base_dir: 项目基础目录
        character_name: 角色名称
        content_image: 要贴入的图片 (PIL.Image.Image)
        background_index: 背景索引 (0-15, 默认0)
        expression_index: 表情索引 (默认0)
        padding: 内边距 (默认12)
        allow_upscale: 是否允许放大 (默认True)
    
    Returns:
        PNG 图片的 bytes
    
    Example:
        >>> img = Image.open("test.jpg")
        >>> png_bytes = generate_image_with_picture(
        ...     base_dir="C:\\path\\to\\project",
        ...     character_name="sherri",
        ...     content_image=img,
        ...     background_index=0,
        ...     expression_index=0
        ... )
    """
    # 获取背景和角色表情
    background, character = get_background_and_character_image(
        base_dir, character_name, background_index, expression_index
    )
    
    # 合并图像
    merged_image = merge_character_to_background(background, character)
    
    # 粘贴图片
    png_bytes = paste_image_auto(
        image_source=merged_image,
        image_overlay=None,
        top_left=TEXT_BOX_CONFIG["top_left"],
        bottom_right=TEXT_BOX_CONFIG["bottom_right"],
        content_image=content_image,
        align="center",
        valign="middle",
        padding=padding,
        allow_upscale=allow_upscale,
        keep_alpha=True,
        role_name=character_name,
        text_configs_dict=TEXT_CONFIGS_DICT,
        base_dir=base_dir
    )
    
    return png_bytes


def get_available_characters() -> list[str]:
    """获取所有可用角色列表"""
    return list(MAHOSHOJO.keys())


def get_character_info(character_name: str) -> dict:
    """获取角色信息"""
    if character_name not in MAHOSHOJO:
        raise ValueError(f"角色不存在: {character_name}")
    return MAHOSHOJO[character_name].copy()


def get_character_id_by_nickname(nickname: str) -> Optional[str]:
    """通过昵称查找角色ID"""
    nickname_lower = nickname.lower()
    for char_id, nicknames in NICKNAME_MAP.items():
        if nickname_lower in [n.lower() for n in nicknames]:
            return char_id
    return None


def get_random_expression(character_name: str, last_expression_index: int = -1) -> int:
    """
    随机获取表情索引（避免连续相同背景）
    
    Args:
        character_name: 角色名称
        last_expression_index: 上一次的表情索引
    
    Returns:
        新的表情索引
    """
    if character_name not in MAHOSHOJO:
        raise ValueError(f"角色不存在: {character_name}")
    
    emotion_count = MAHOSHOJO[character_name]["emotion_count"]
    
    if last_expression_index == -1:
        return random.randint(0, emotion_count - 1)
    
    # 避免背景相同
    last_bg = last_expression_index // 16
    max_attempts = 100
    
    for _ in range(max_attempts):
        new_idx = random.randint(0, emotion_count - 1)
        new_bg = new_idx // 16
        if new_bg != last_bg:
            return new_idx
    
    return random.randint(0, emotion_count - 1)


# ==================== 示例与测试 ====================

if __name__ == "__main__":
    print("Manosaba Plugin - 魔法少女贴图生成器")
    print("=" * 50)
    print("\n可用角色:")
    for char in get_available_characters():
        info = get_character_info(char)
        print(f"  - {char}: {info['emotion_count']} 个表情")
    
    print("\n\n主要接口函数:")
    print("  - generate_image_with_text(base_dir, character_name, text, ...)")
    print("  - generate_image_with_picture(base_dir, character_name, image, ...)")
    print("  - get_available_characters()")
    print("  - get_character_info(character_name)")
    print("  - get_character_id_by_nickname(nickname)")
    print("  - get_random_expression(character_name, last_expression_index)")

    print("\n\n测试昵称查找:")
    print(f"  '安安' -> {get_character_id_by_nickname('安安')}")
    print(f"  'sherri' -> {get_character_id_by_nickname('sherri')}")
    print(f"  '不存在' -> {get_character_id_by_nickname('不存在')}")
