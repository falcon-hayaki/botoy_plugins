from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from io import BytesIO
import requests as req
import base64

resource_path = "./resources/img_text"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "PicMsg":
        content = json.loads(ctx.Content)
        if 'Content' in content:
            text = content['Content']
            if text[0:3] == '加字 ' and len(text) > 3:
                n = 0
                for i in text[3:]:
                    if i == ' ':
                        n += 1
                text_add = text[3:] + ' '*n
                img_type = addText(text_add, content['GroupPic'][0]['Url'])
                pic_path = os.path.join(resource_path, 'image.') + img_type
                pic = picToBase64(pic_path)
                bot.sendGroupPic(ctx.FromGroupId, picBase64Buf=pic)

def addText(text, url):
    response = req.get(url)
    im = Image.open(BytesIO(response.content))

    img_type = im.format

    if img_type == "GIF":
        frames = []
        for frame in ImageSequence.Iterator(im):
            frame = addTextInFrame(frame, text)
            b = BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)
            frames.append(frame)

        img_path = os.path.join(resource_path, 'image.') + img_type
        frames[0].save(img_path, save_all = True, append_images=frames[1:])

    else:
        bg = addTextInFrame(im, text)
        
        img_path = os.path.join(resource_path, 'image.') + img_type
        bg.save(img_path)
    
    return img_type

def addTextInFrame(frame, text):
    font_size = 200
    font = ImageFont.truetype(os.path.join(resource_path, "font/FZCDXJW.TTF"), font_size)
    text_size = font.getsize(text)
    while text_size[0] > frame.size[0]*4/5:
        font_size -= 1
        font = ImageFont.truetype(os.path.join(resource_path, "font/FZCDXJW.TTF"), font_size)
        text_size = font.getsize(text)

    bg_size = (frame.size[0], frame.size[1]+text_size[1])
    bg = Image.new("RGB", bg_size, color = (255, 255, 255))
    bg.paste(frame, (0, 0))

    fillcolor = "black"

    print(frame.size)
    print(text_size)
    print(text)
    print(len(text))
    text_coordinate = (int((frame.size[0]-text_size[0])/2), int(frame.size[1]))
    print(text_coordinate)

    draw = ImageDraw.Draw(bg)
    draw.text(text_coordinate, text, font = font, fill = fillcolor)
    del draw

    return bg

def picToBase64(pic_path):
    with open(pic_path, 'rb') as f:
        pic = f.read()
    return str(base64.b64encode(pic), encoding = 'utf-8')