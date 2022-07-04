from botoy import Botoy, Action, GroupMsg
from botoy import decorators as deco
import os
import json
import requests
import random
import time

# TODO: 搜过的图保存至本地
resource_path = "./resources/get_pixiv_img"

bot = Action(
    qq = int(os.getenv('BOTQQ'))
)
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == "TextMsg":
        content_list = ctx.Content.strip().split(sep = " ")
        if content_list[0] == "取图":
            try:
                id_str = ctx.Content.strip().split(sep = " ")[1]
                int(id_str)
            except:
                if id_str == "随机":
                    rand_id = str(random.randint(10000000, 99999999))
                    p = pixiv(rand_id, "img")
                    img_list = p.get_img_via_img_id()
                    while img_list == "img_id error":
                        rand_id = str(random.randint(10000000, 99999999))
                        p = pixiv(rand_id, "img")
                        img_list = p.get_img_via_img_id()
                    for img in img_list:
                        bot.sendGroupPic(ctx.FromGroupId, picUrl=img)
                        time.sleep(0.3)
                    bot.sendGroupText(ctx.FromGroupId, content=f"https://www.pixiv.net/artworks/{rand_id}")
                else:
                    bot.sendGroupText(ctx.FromGroupId, content="格式有误")
            else:
                id_type = "none"
                if len(id_str) == 8:
                    id_type = "img"
                elif len(id_str) == 7:
                    id_type = "artist"

                p = pixiv(id_str, id_type)

                if id_type == "img":
                    img_list = p.get_img_via_img_id()
                    if img_list == "network error":
                        bot.sendGroupText(ctx.FromGroupId, content="连接至pixiv服务器失败")
                    elif img_list == "img_id error":
                        bot.sendGroupText(ctx.FromGroupId, content="输入id有误")
                    else:
                        for img in img_list:
                            bot.sendGroupPic(ctx.FromGroupId, picUrl=img)
                        bot.sendGroupText(ctx.FromGroupId, content=f"https://www.pixiv.net/artworks/{id_str}")
                elif id_type == "artist":
                    pass


# pixiv API
class pixiv():
    def __init__(self, id, id_type):
        self.id = id
        self.img_id_url = ""
        self.artist_id_url = ""
        if id_type == "img":
            self.img_id_url = f"https://www.pixiv.net/ajax/illust/{self.id}/pages?lang=zh"
        else:
            # TODO: 根据作者搜图
            pass

    def get_img_via_img_id(self):
        try:
            data = requests.get(self.img_id_url)
            print(data)
        except:
            return "network error"
        else:
            data_dict = json.loads(data.text)
            if data_dict['error']:
                return "img_id error"
            else:
                img_list = []
                for imgs in data_dict['body']:
                    img_list.append(imgs['urls']['regular'])
                return img_list

    def get_img_via_artist_id(self):
        pass