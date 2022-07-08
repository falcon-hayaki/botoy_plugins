from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
from PIL import Image, ImageDraw, ImageFont
import os
import json
import random
import datetime
import base64

from utils.fileio import read_json, write_json, picToBase64

resource_path = "./resources/hanayori_draw"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)

@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == 'TextMsg':
        if ctx.Content in ['抽签', '抽签签', '我的回合，抽签', '我的回合，抽签！']:
            texts = read_json(os.path.join(resource_path, "fortune/copywriting.json"))
            titles = read_json(os.path.join(resource_path, "fortune/goodLuck.json"))
            date_list = str(datetime.date.today()).split(sep='-')
            seed = ''
            for date in date_list:
                seed += date
            seed = int(seed)
            seed += ctx.FromUserId
            random.seed(seed)
            choice = random.choice(range(1, 12))
            random.seed(seed)
            text = random.choice(texts['copywriting'])
            for title in titles["types_of"]:
                if title["good-luck"] == text["good-luck"]:
                    break
            text = text["content"]
            title = title["name"]
            pic_chosen = os.path.join(resource_path, 'img/frame_%d.png' % choice)
            pic_path = draw_card(pic_chosen, title, text, ctx.FromUserId)
            pic = picToBase64(pic_path)
            content = "[PICFLAG]{}今天的运势".format(ctx.FromNickName)
            content = f"{ctx.FromNickName}今天的运势"
            bot.sendGroupPic(ctx.FromGroupId, picBase64Buf=pic, content=content)

            #风控临时添加
#             FRAME_DICT = ['泳装花丸', '泳装ののの', '泳装小东', '泳装鹿乃', '一周目新年鹿乃', '一周目新年ののの', '一周目新年小东', '一周目新年花丸', '二周目新年花丸', '二周目新年小东', '二周目新年鹿乃']
#             content = f"{ctx.FromNickName}今天的运势是:\n[{FRAME_DICT[choice-1]}][{title}]{text}.jpg\n* 有的图被风控了发不出来，暂时还没解决这个问题，先临时发文字吧。"
#             bot.sendGroupText(ctx.FromGroupId, content=content)
        elif ctx.Content.strip().split()[0] == "添加签":
            args = ctx.Content.strip().split()[1:]
            if args:
                errflag = ""
                if len(args) != 2:
                    errflag = "格式有误"
                else:
                    goodLuck = f'{resource_path}/fortune/goodLuck.json'
                    copywrighting = f'{resource_path}/fortune/copywriting.json'
                    lucks = read_json(goodLuck)
                    m1s = []
                    for luck in lucks["types_of"]:
                        m1s.append(luck["name"])
                    if args[0] not in m1s:
                        errflag = "未在运势列表"
                    elif len(args[1]) > 36:
                        errflag = "事件不能超过36字"
                    else:
                        if ctx.FromGroupId == 1014696092:
                            cw = read_json(copywrighting)
                            new_cw = {}
                            new_cw["good-luck"] = lucks["types_of"][m1s.index(args[0])]["good-luck"]
                            new_cw["content"] = args[1]
                            cw["copywriting"].append(new_cw)
                            write_json(copywrighting, cw)
                            bot.sendGroupText(ctx.FromGroupId, "已添加")
                        else:
                            m = f'来自{ctx.FromGroupName}({ctx.FromGroupId})的{ctx.FromNickName}({ctx.FromUserId})提交的签\n添加签 {args[0]} {args[1]}'
                            bot.sendFriendText(1511603275, m)
                            bot.sendGroupText(ctx.FromGroupId, "已提交")
                if errflag:
                    bot.sendGroupText(ctx.FromGroupId, errflag)
            else:
                goodLuck = f'{resource_path}/fortune/goodLuck.json'
                copyrighting = f'{resource_path}/fortune/copywriting.json'
                lucks = read_json(goodLuck)
                m1s = []
                for luck in lucks["types_of"]:
                    m1s.append(luck["name"])
                m = "1. 运势："
                for m1 in m1s:
                    m += m1 + "，"
                m = m[:-1]
                m += "\n2. 事件不能超过36个字\n3. 格式：添加签 运势 事件；如：添加签 仕事運 适合在家打一整天轴；注：繁简体敏感\n4. 并不是立即添加而是提交审核，最终解释权归falcon所有。"
                bot.sendGroupText(ctx.FromGroupId, m)

def draw_card(pic_chosen, title, text, from_user):
    fontPath = {
        'title': f'{resource_path}/font/Mamelon.otf',
        'text': f'{resource_path}/font/sakura.ttf'
    }
    imgPath = pic_chosen

    img = Image.open(imgPath)

    # Draw title
    draw = ImageDraw.Draw(img)
    font_size = 45
    color = '#F5F5F5'
    image_font_center = (140, 99)
    ttfront = ImageFont.truetype(fontPath['title'], font_size)
    font_length = ttfront.getsize(title)
    draw.text((image_font_center[0]-font_length[0]/2, image_font_center[1]-font_length[1]/2),
                title, fill=color,font=ttfront)
    # Text rendering
    font_size = 25
    color = '#323232'
    image_font_center = [140, 297]
    ttfront = ImageFont.truetype(fontPath['text'], font_size)
    result = decrement(text)
    if not result[0]:
        return 
    textVertical = []
    for i in range(0, result[0]):
        font_height = len(result[i + 1]) * (font_size + 4)
        textVertical = vertical(result[i + 1])
        x = int(image_font_center[0] + (result[0] - 2) * font_size / 2 + 
                (result[0] - 1) * 4 - i * (font_size + 4))
        y = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), textVertical, fill = color, font = ttfront)
    # Save
    outPath = f'{resource_path}/out/{from_user}.png'
    img.save(outPath)
    return outPath

def decrement(text):
    length = len(text)
    result = []
    cardinality = 9
    if length > 4 * cardinality:
        return [False]
    numberOfSlices = 1
    while length > cardinality:
        numberOfSlices += 1
        length -= cardinality
    result.append(numberOfSlices)
    # Optimize for two columns
    space = ' '
    length = len(text)
    if numberOfSlices == 2:
        if length % 2 == 0:
            # even
            fillIn = space * int(9 - length / 2)
            return [numberOfSlices, text[:int(length / 2)] + fillIn, fillIn + text[int(length / 2):]]
        else:
            # odd number
            fillIn = space * int(9 - (length + 1) / 2)
            return [numberOfSlices, text[:int((length + 1) / 2)] + fillIn,
                                    fillIn + space + text[int((length + 1) / 2):]]
    for i in range(0, numberOfSlices):
        if i == numberOfSlices - 1 or numberOfSlices == 1:
            result.append(text[i * cardinality:])
        else:
            result.append(text[i * cardinality:(i + 1) * cardinality])
    return result

def vertical(str):
    list = []
    for s in str:
        list.append(s)
    return '\n'.join(list)