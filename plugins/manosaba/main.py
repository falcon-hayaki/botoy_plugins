import os
import re
import random

import logging
logger = logging.getLogger(__name__)

from botoy import ctx, S, file_to_base64

# 插件资源路径
resource_path = 'resources/manosaba'
from .manosaba_plugin import (
    generate_image_with_text,
    get_character_id_by_nickname,
    get_random_expression,
    get_available_characters,
)

async def manosaba_command():
    if msg := (ctx.g or ctx.f):
        match = re.match(r"^(?:魔裁|manosaba)\s*(\S+)\s+(.+)", msg.text.strip(), re.DOTALL)
        if not match:
            return

        nickname, text = match.groups()

        if not text:
            return

        if nickname in ['随机', '随便', '任意', 'random']:
            character_id = random.choice(get_available_characters())
        else:
            character_id = get_character_id_by_nickname(nickname)
        if not character_id:
            return

        try:
            # 随机背景和表情
            background_index = random.randint(0, 15)
            expression_index = get_random_expression(character_id)

            # 生成图片
            png_bytes = generate_image_with_text(
                base_dir=resource_path,
                character_name=character_id,
                text=text,
                background_index=background_index,
                expression_index=expression_index,
            )

            # 保存图片
            temp_dir = os.path.join(resource_path, "temp_generated_imgs")
            os.makedirs(temp_dir, exist_ok=True)
            pic_path = os.path.join(temp_dir, f"{msg.from_user}.png")
            
            with open(pic_path, "wb") as f:
                f.write(png_bytes)
            
            # 发送图片
            await S.image(data=file_to_base64(pic_path), text='')

        except Exception as e:
            # pass
            # await S.text(f"生成失败: {e}")
            logger.exception(f'monoaba error')
