import requests
import pytz
import json
import os
import random
import gevent
from datetime import datetime
from bot import action
from utils.fileio import read_json, write_json

class Timing():
    def __init__(self):
        self.msg_queue = []
        self.jobs = ['bili_dynamic', 'bili_live_alarm', 'msg_sender', 'draw_card_seed']
        
    def start(self):
        for name in self.jobs:
            self.start_background_task(getattr(self, name))
        
    def start_background_task(self, f, *args, **kwargs):
        gevent.spawn(f, *args, **kwargs).start()
    
    # ----------------------------- functions -----------------------------
    def msg_sender(self, interval=2):
        while True:
            if self.msg_queue:
                msg = self.msg_queue[0]
                try:
                    if "text" in msg:
                        action.sendGroupText(msg["group"], msg["text"])
                    if "imgs" in msg:
                        for img in msg["imgs"]:
                            if img:
                                action.sendGroupPic(msg["group"], picUrl=img)
                    del self.msg_queue[0]
                except:
                    action.sendGroupText(1014696092, "bot危，速来")
            gevent.sleep(interval)

    def bili_dynamic(self, interval=1):
        while True:
            resource_path = "resources/bili_dynamic"
            subscribes = read_json(os.path.join(resource_path, "subscribes_list.json"))
            data = read_json(os.path.join(resource_path, "dynamic_data.json"))
            for uid in subscribes:
                init = False
                if uid not in data:
                    data[uid] = {
                        "uname": "",
                        "face": "",
                        "sign": "",
                        "cards": {}
                    }
                    init = True
                dynamic = self.get_api_responce(uid)
                if not dynamic:
                    continue
                cards = {}
                if "cards" not in dynamic['data']:
                    info = self.get_up_info(uid)['data']['card']
                    data[uid]["uname"] = info["name"]
                    data[uid]["face"] = info["face"]
                    data[uid]["sign"] = info["sign"]
                    continue
                # format cards
                for card in dynamic['data']['cards']:
                    dynamic_id = str(card["desc"]["dynamic_id"])
                    cards[dynamic_id] = {
                        "type": card["desc"]["type"],
                        "rid": card["desc"]["rid"]
                    }
                    card_dict = json.loads(card["card"])
                    if card["desc"]["type"] == 4:
                        cards[dynamic_id]["text"] = card_dict["item"]["content"]
                    elif card["desc"]["type"] == 2:
                        cards[dynamic_id]["text"] = card_dict["item"]["description"]
                        cards[dynamic_id]["pictures"] = card_dict["item"]["pictures"]
                    elif card["desc"]["type"] == 8:
                        cards[dynamic_id]["bvid"] = card["desc"]["bvid"]
                        cards[dynamic_id]["title"] = card_dict["title"]
                        cards[dynamic_id]["pic"] = card_dict["pic"]
                    elif card["desc"]["type"] == 64:
                        cards[dynamic_id]["origin_image_urls"] = card_dict["origin_image_urls"]
                        cards[dynamic_id]["title"] = card_dict["title"]
                        cards[dynamic_id]["words"] = card_dict["words"]
                info = self.get_up_info(uid)['data']['card']
                status = {}
                status["uname"] = info["name"]
                status["face"] = info["face"]
                status["sign"] = info["sign"]
                
                if init:
                    for key in status:
                        data[uid][key] = status[key]
                    data[uid]['cards'] = cards
                    continue
                else:
                    for key in status:
                        if data[uid][key] != status[key]:
                            if key == "face":
                                if status[key].split(sep = "/")[-1] != data[uid][key].split(sep = "/")[-1]:
                                    for group in subscribes[uid]['groups']:
                                        t = f"你关注的{status['uname']}更新了{key}: "
                                        m = {
                                            "group": group,
                                            "text": t,
                                            "imgs": [status[key]]
                                        }
                                        self.msg_queue.append(m)
                            elif key == "sign":
                                for group in subscribes[uid]['groups']:
                                    t = f"你关注的{status['uname']}更新了{key}: \n{status[key]}"
                                    m = {
                                        "group": group,
                                        "text": t
                                    }
                                    self.msg_queue.append(m)
                        data[uid][key] = status[key]
                    for card in cards:
                        if card not in data[uid]['cards']:
                            if cards[card]['type'] == 4:
                                for group in subscribes[uid]['groups']:
                                    url = f"https://t.bilibili.com/{card}?tab=2"
                                    t = f"你关注的{status['uname']}发了新动态: \n{cards[card]['text']}\n{url}"
                                    m = {
                                        "group": group,
                                        "text": t
                                    }
                                    self.msg_queue.append(m)
                            elif cards[card]['type'] == 2:
                                for group in subscribes[uid]['groups']:
                                    url = f"https://t.bilibili.com/{card}?tab=2"
                                    t = f"你关注的{status['uname']}发了新动态: \n{cards[card]['text']}\n{url}"
                                    img_list = []
                                    for img_src in cards[card]["pictures"]:
                                        img_list.append(img_src["img_src"])
                                    m = {
                                        "group": group,
                                        "text": t,
                                        "imgs": img_list
                                    }
                                    self.msg_queue.append(m)
                            elif cards[card]["type"] == 8:
                                for group in subscribes[uid]['groups']:
                                    url = f"https://www.bilibili.com/video/{cards[card]['bvid']}"
                                    t = f"你关注的{status['uname']}发了新视频: \n{cards[card]['title']}\n{url}"
                                    m = {
                                        "group": group,
                                        "text": t,
                                        "imgs": [cards[card]["pic"]]
                                    }
                                    self.msg_queue.append(m)
                            elif cards[card]["type"] == 64:
                                for group in subscribes[uid]['groups']:
                                    url = f"https://www.bilibili.com/read/cv{cards[card]['rid']}"
                                    t = f"你关注的{status['uname']}发了新专栏: \n{cards[card]['title']}\n字数：{cards[card]['words']}\n{url}"
                                    m = {
                                        "group": group,
                                        "text": t,
                                        "imgs": cards[card]["origin_image_urls"]
                                    }
                                    self.msg_queue.append(m)
                        else:
                            break
                    data[uid]['cards'] = cards
            uid_to_del = []
            for uid in data:
                if uid not in subscribes:
                    uid_to_del.append(uid)
            for uid in uid_to_del:
                del data[uid]
            write_json(os.path.join(resource_path, "dynamic_data.json"), data)
            
            gevent.sleep(interval)

    def bili_live_alarm(self, interval=1):
        while True:
            resource_path = "resources/bili_live_alarm"
            subscribes = read_json(os.path.join(resource_path, "subscribes.json"))
            status = read_json(os.path.join(resource_path, "bili_live_status.json"))
            for roomid in subscribes:
                if roomid not in status:
                    status[roomid] = {
                        "uname": "",
                        "status": 0,
                        "title": "",
                        "img": ""
                    }
                current_status, title, img, uid = self.get_live_status(roomid)
                old_status = status[roomid]["status"]
                if title:
                    print(title)
                else:
                    print("none")
                print("current:" + str(current_status) + "\nold" + str(old_status))
                if title == "-412 error":
                    m = {
                        "group": 1014696092,
                        "text": "醒醒，开播提醒被风控了",
                    }
                    self.msg_queue.append(m)
                    continue
                elif current_status == old_status:
                    continue
                else:
                    if current_status == 1:
                        if not status[roomid]["uname"]:
                            uname = self.get_uname(uid)
                            if uname == "-412 error":
                                m = {
                                    "group": 1014696092,
                                    "text": "醒醒，uid API被风控了",
                                }
                                self.msg_queue.append(m)
                                continue
                            status[roomid]["uname"] = uname
                        status[roomid]["status"] = current_status
                        status[roomid]["title"] = title
                        status[roomid]["img"] = img
                        status[roomid]["start_time"] = str(datetime.now(tz=pytz.timezone("Asia/Shanghai")))
                        status[roomid]["end_time"] = ''
                        status[roomid]['checkpoints'] = []
                        for group in subscribes[roomid]['groups']:
                            url = f"https://live.bilibili.com/{roomid}"
                            t = f"{status[roomid]['uname']}开播了！\n标题：{title}\n{url}"
                            m = {
                                "group": group,
                                "text": t,
                                "imgs": [img]
                            }
                            self.msg_queue.append(m)

                    elif current_status == 0:
                        status[roomid]["status"] = current_status
                        status[roomid]["end_time"] = str(datetime.now(tz=pytz.timezone("Asia/Shanghai")))
                        try:
                            start_time = datetime.strptime(str(status[roomid]["start_time"])[:-6], "%Y-%m-%d %H:%M:%S.%f")
                            end_time = datetime.strptime(str(status[roomid]["end_time"])[:-6], "%Y-%m-%d %H:%M:%S.%f")
                            t = f'{status[roomid]["title"]}已结束，开始时间：{status[roomid]["start_time"]}， 结束时间：{status[roomid]["end_time"]}'
                            if 'checkpoints' in status[roomid] and status[roomid]['checkpoints']:
                                t += '\n剪辑点：\n'
                                for data in status[roomid]['checkpoints']:
                                    check_time = datetime.strptime(str(data["time"])[:-6], "%Y-%m-%d %H:%M:%S.%f")
                                    if check_time > end_time or check_time < start_time:
                                        m = {
                                            "group": 1014696092,
                                            "text": "时空遭到逆转",
                                        }
                                        self.msg_queue.append(m)
                                    else:
                                        t += str(check_time - start_time) + "\t" + data["text"] + "\n"
                            else:
                                pass
                            for group in subscribes[roomid]['groups']:
                                m = {
                                    "group": group,
                                    "text": t,
                                }
                                self.msg_queue.append(m)
                        except Exception as e:
                            t = f"checkpoint功能故障，房间号: {roomid}\n{e}"
                            m = {
                                "group": 1014696092,
                                "text": t,
                            }
                            self.msg_queue.append(m)

            roomid_to_del = []
            for roomid in status:
                if roomid not in subscribes:
                    roomid_to_del.append(roomid)
            for roomid in roomid_to_del:
                del status[roomid]
            write_json(os.path.join(resource_path, "bili_live_status.json"), status)
            gevent.sleep(interval)

    def draw_card_seed(self, interval=60*10):
        while True:
            seed = str(random.randint(1, 1145141919))
            print("current seed:")
            print(seed)
            os.environ['cardSeed'] = seed
            gevent.sleep(interval)
    # ----------------------------- tasks -----------------------------
        
    # ----------------------------- functions -----------------------------
    def get_uname(self, uid):
        url = f"http://api.bilibili.com/x/web-interface/card?mid={uid}&jsonp=jsonp"
        html = requests.get(url)
        gevent.sleep(0.5)
        data = json.loads(html.text)
        if data['code'] == -412:
            return "-412 error"
        return data['data']['card']['name']
        
    def get_live_status(self, room_id):
        url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
        html = requests.get(url)
        data = json.loads(html.text)
        gevent.sleep(0.5)
        if data['code'] != 0:
            return [0, "-412 error", "", ""]
        if data["data"]["live_status"] == 1:
            return [1, data['data']['title'], data['data']['user_cover'], data['data']['uid']]
        else:
            return [0, data['data']['title'], data['data']['user_cover'], data['data']['uid']]
    
    def get_up_info(self, uid):
        url = f"http://api.bilibili.com/x/web-interface/card?mid={uid}&jsonp=jsonp"
        html = requests.get(url)
        gevent.sleep(1)
        data = json.loads(html.text)
        return data
    
    def get_api_responce(self, uid):
        url = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={uid}&offset_dynamic_id=0&need_top=0"
        html = requests.get(url)
        gevent.sleep(1)
        html.encoding = "utf-8"
        html_dict = json.loads(html.text)
        if html_dict['code'] != 0:
            m = {
                "group": 1014696092,
                "text": f"dynamic error code: {html_dict['code']}",
            }
            self.msg_queue.append(m)
            return False
        try:
            print(html_dict["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"])
        except:
            t = f"\033[1;31m Error: {uid} \033[0m"
            print(t)
            print(html_dict)
            m = {
                "group": 1014696092,
                "text": f"{uid}动态获取失败，请检查log",
            }
            self.msg_queue.append(m)
        print(html_dict["code"])
        return html_dict
    # ----------------------------- functions -----------------------------
    