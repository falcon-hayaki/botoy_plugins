import time
import requests
import pytz
import json
import os
import random
from datetime import datetime
from bot import action

class Timing():
    def __init__(self):
        self.msg_queue = []
    
    def msg_sender(self):
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

    def bili_dynamic(self):
        def get_api_responce(uid):
            url = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={uid}&offset_dynamic_id=0&need_top=0"
            html = requests.get(url)
            time.sleep(1)
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

        def get_up_info(uid):
            url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}&jsonp=jsonp"
            html = requests.get(url)
            time.sleep(1)
            data = json.loads(html.text)
            return data

        def new_subscribe(uid, data):
            data[uid] = {
                "uname": "",
                "face": "",
                "sign": "",
                "cards": {}
            }
            return data

        def check_news(uid, init, data, subscribes):
            dynamic = get_api_responce(uid)
            if not dynamic:
                return data
            cards = {}
            if "cards" not in dynamic['data']:
                info = get_up_info(uid)['data']
                data[uid]["uname"] = info["name"]
                data[uid]["face"] = info["face"]
                data[uid]["sign"] = info["sign"]
                return data

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
            info = get_up_info(uid)['data']
            status = {}
            status["uname"] = info["name"]
            status["face"] = info["face"]
            status["sign"] = info["sign"]
            
            if init:
                for key in status:
                    data[uid][key] = status[key]
                data[uid]['cards'] = cards
                return data
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
                return data

        resource_path = "resources/bili_dynamic"

        with open(os.path.join(resource_path, "subscribes_list.json"), 'rb') as f:
            subscribes = json.load(f)
            f.close()
        with open(os.path.join(resource_path, "dynamic_data.json"), 'rb') as f:
            data = json.load(f)
            f.close()

        self.bili_dynamic_subnum = len(subscribes)

        for uid in subscribes:
            init = False
            if uid not in data:
                data = new_subscribe(uid, data)
                init = True
            data = check_news(uid, init, data, subscribes)
            time.sleep(3*60/self.bili_dynamic_subnum)

        uid_to_del = []
        for uid in data:
            if uid not in subscribes:
                uid_to_del.append(uid)
        for uid in uid_to_del:
            del data[uid]
        
        with open(os.path.join(resource_path, "dynamic_data.json"), 'w') as f:
            json.dump(data, f)
            f.close()

    def bili_live_alarm(self):
        def get_live_status(room_id):
            url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
            html = requests.get(url)
            data = json.loads(html.text)
            time.sleep(0.5)
            if data['code'] != 0:
                return [0, "-412 error", "", ""]
            if data["data"]["live_status"] == 1:
                return [1, data['data']['title'], data['data']['user_cover'], data['data']['uid']]
            else:
                return [0, data['data']['title'], data['data']['user_cover'], data['data']['uid']]
        
        def get_uname(uid):
            url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}&jsonp=jsonp"
            html = requests.get(url)
            time.sleep(0.5)
            data = json.loads(html.text)
            if data['code'] == -412:
                return "-412 error"
            return data['data']['name']
            
        def new_subscribe(status, roomid):
            status[roomid] = {
                "uname": "",
                "status": 0,
                "title": "",
                "img": ""
            }
            return status
        
        def status_check(status, subscribes, roomid):
            current_status, title, img, uid = get_live_status(roomid)
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
                return status
            elif current_status == old_status:
                return status
            elif current_status != old_status:
                if current_status == 1:
                    if not status[roomid]["uname"]:
                        uname = get_uname(uid)
                        if uname == "-412 error":
                            m = {
                                "group": 1014696092,
                                "text": "醒醒，uid API被风控了",
                            }
                            self.msg_queue.append(m)
                            return status
                        status[roomid]["uname"] = uname
                    status[roomid]["status"] = current_status
                    status[roomid]["title"] = title
                    status[roomid]["img"] = img
                    for group in subscribes[roomid]['groups']:
                        url = f"https://live.bilibili.com/{roomid}"
                        t = f"{status[roomid]['uname']}开播了！\n标题：{title}\n{url}"
                        m = {
                            "group": group,
                            "text": t,
                            "imgs": [img]
                        }
                        self.msg_queue.append(m)

                    with open("resources/bili_live_checkpoint/subscribes.json", 'rb') as f:
                        checkpoints = json.load(f)
                    if roomid in checkpoints:
                        checkpoints[roomid]["status"] = 1
                        checkpoints[roomid]["title"] = title
                        checkpoints[roomid]["start_time"] = str(datetime.now(tz=pytz.timezone("Asia/Shanghai")))
                        with open("resources/bili_live_checkpoint/subscribes.json", 'w') as f:
                            json.dump(checkpoints, f)

                elif current_status == 0:
                    status[roomid]["status"] = current_status
                    status[roomid]["title"] = ""
                    status[roomid]["img"] = ""

                    with open("resources/bili_live_checkpoint/subscribes.json", 'rb') as f:
                        checkpoints = json.load(f)
                    if roomid in checkpoints:
                        checkpoints[roomid]["status"] = 0
                        checkpoints[roomid]["end_time"] = str(datetime.now(tz=pytz.timezone("Asia/Shanghai")))
                        with open("resources/bili_live_checkpoint/subscribes.json", 'w') as f:
                            json.dump(checkpoints, f)

                        with open("resources/bili_live_checkpoint/checkpoints.json", 'rb') as f:
                            checkpoints_data = json.load(f)
                        if roomid not in checkpoints_data:
                            checkpoints_data[roomid] = []
                        try:
                            start_time = datetime.strptime(str(checkpoints[roomid]["start_time"])[:-6], "%Y-%m-%d %H:%M:%S.%f")
                            end_time = datetime.strptime(str(checkpoints[roomid]["end_time"])[:-6], "%Y-%m-%d %H:%M:%S.%f")
                            t = f'{checkpoints[roomid]["title"]}已结束，开始时间：{checkpoints[roomid]["start_time"]}， 结束时间：{checkpoints[roomid]["end_time"]}\n剪辑点：\n'
                            if checkpoints_data[roomid]:
                                for data in checkpoints_data[roomid]:
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
                                t += "无"
                            for group in checkpoints[roomid]["groups"]:
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
                        checkpoints_data[roomid] = []
                        with open("resources/bili_live_checkpoint/checkpoints.json", 'w') as f:
                            json.dump(checkpoints_data, f)

            return status

        resource_path = "resources/bili_live_alarm"

        with open(os.path.join(resource_path, "subscribes.json"), 'rb') as f:
            subscribes = json.load(f)
            f.close()
        with open(os.path.join(resource_path, "bili_live_status.json"), 'rb') as f:
            status = json.load(f)
            f.close()

        for roomid in subscribes:
            if roomid not in status:
                status = new_subscribe(status, roomid)
            status = status_check(status, subscribes, roomid)

        roomid_to_del = []
        for roomid in status:
            if roomid not in subscribes:
                roomid_to_del.append(roomid)
        for roomid in roomid_to_del:
            del status[roomid]

        with open(os.path.join(resource_path, "bili_live_status.json"), 'w') as f:
            json.dump(status, f)
            f.close()

    def draw_card_seed(self):
        seed = str(random.randint(1, 1145141919))
        print("current seed:")
        print(seed)
        os.environ['cardSeed'] = seed

    def danmu_monitor(self):
        def api_viewer(uid):
            url = f"https://api.neeemooo.com/viewer/{uid}"
            headers = {"origin": "https://matsuri.icu"}
            return json.loads(requests.get(url, headers = headers).text)

        def check_new(uid, data, subscribes):
            current = api_viewer(uid)
            if current["status"] == 0:
                current_data = current["data"]
                print("正在监听")
                print(current_data[0]["full_comments"][0]["username"])
                if not data[uid]:
                    data[uid] = current_data
                else:
                    for card in current_data:
                        if card not in data[uid]:
                            print("\ntest\n")
                            count = 0
                            t = f'{card["full_comments"][0]["username"]}曾出现在{card["clip_info"]["name"]}的直播 {card["clip_info"]["title"]} 中：\n'
                            for comment in card["full_comments"]:
                                l = ""
                                if "text" in comment:
                                    if "superchat_price" in comment:
                                        l += "sc: "
                                    l += comment["text"]
                                    l += "\n"
                                elif "gift_name" in comment:
                                    l += "送出" + comment["gift_name"] + " x" + str(comment["gift_num"]) + "\n"
                                t += l
                                count += 1
                                if count == 5:
                                    for group in subscribes[uid]["groups"]:
                                        m = {
                                            "group": group,
                                            "text": t[:-1]
                                        }
                                        self.msg_queue.append(m)
                                        count = 0
                                        t = ""
                            if t:
                                for group in subscribes[uid]["groups"]:
                                    m = {
                                        "group": group,
                                        "text": t[:-1]
                                    }
                                    self.msg_queue.append(m)
                                    count = 0
                                    t = ""
                    data[uid] = current_data
            else:
                action.sendGroupText(1014696092, "danmu monitor API异常")

            return data

        resource_path = "resources/danmu_monitor"

        with open(os.path.join(resource_path, "subscribes.json"), 'rb') as f:
            subscribes = json.load(f)
            f.close()
        with open(os.path.join(resource_path, "danmu_data.json"), 'rb') as f:
            data = json.load(f)
            f.close()

        for uid in subscribes:
            if uid not in data:
                data[uid] = []
            data = check_new(uid, data, subscribes)

        roomid_to_del = []
        for roomid in data:
            if roomid not in subscribes:
                roomid_to_del.append(roomid)
        for roomid in roomid_to_del:
            del data[roomid]

        with open(os.path.join(resource_path, "danmu_data.json"), 'w') as f:
            json.dump(data, f)
            f.close()

    def danmu_send(self):
        def send(room_id, msg):
            url = 'https://api.live.bilibili.com/msg/send'
            data = {
                'color': '16777215',
                'fontsize': '25',
                'mode': '1',
                'msg': msg,
                'rnd': str(int(time.time())),
                'roomid': room_id,
                'bubble': '0',
                'csrf_token': 'bc3ca64a45fc9ffe0982b5feba119bc1',
                'csrf': 'bc3ca64a45fc9ffe0982b5feba119bc1'
            }
            headers = {
                'cookie': "LIVE_BUVID=AUTO2716217597445981; _uuid=E57517E3-9B52-D19B-8B5A-6081CF0A2C3A49256infoc; buvid3=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp_plain=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(u)lukuYYJ~0J'uYkk))|kmJ; fingerprint=6fc5b3a08534cdd60c03bad6c6b13a83; SESSDATA=59e52819%2C1642557719%2Cd96be%2A71; bili_jct=543779f554e21b08eddb4d4cbdf660c1; DedeUserID=538828088; DedeUserID__ckMd5=f96ed607acbe97ad; sid=ii8aeooe; bp_t_offset_538828088=550125846804497333; _dfcaptcha=7e770e50e44b90f3f4ed8415b7d9cbe4; PVID=3LIVE_BUVID=AUTO2716217597445981; _uuid=E57517E3-9B52-D19B-8B5A-6081CF0A2C3A49256infoc; buvid3=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp_plain=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(u)lukuYYJ~0J'uYkk))|kmJ; fingerprint=6fc5b3a08534cdd60c03bad6c6b13a83; SESSDATA=59e52819%2C1642557719%2Cd96be%2A71; bili_jct=543779f554e21b08eddb4d4cbdf660c1; DedeUserID=538828088; DedeUserID__ckMd5=f96ed607acbe97ad; sid=ii8aeooe; bp_t_offset_538828088=550125846804497333; _dfcaptcha=7e770e50e44b90f3f4ed8415b7d9cbe4; PVID=3",
                'origin': 'https://live.bilibili.com',
                'referer': 'https://live.bilibili.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
            }
            response = requests.post(url=url, data=data, headers=headers)
            resp_data = json.loads(response.text)
            if resp_data["code"] != 0:
                m = {
                    "group": 1014696092,
                    "text": response.text
                }
                self.msg_queue.append(m)

        resource_path = "resources/danmu_send"
        live_resource_path = "resources/bili_live_alarm"

        with open(os.path.join(resource_path, "data.json"), 'rb') as f:
            data = json.load(f)
            f.close()

        with open(os.path.join(live_resource_path, "bili_live_status.json"), 'rb') as f:
            status = json.load(f)
            f.close()
        
        for room_id in data:
            if room_id in status:
                if status[room_id]["status"] == 1:
                    send(room_id, random.choice(data[room_id]["msg"]))

    def uu_reminder(self):
        def send(room_id, msg):
            url = 'https://api.live.bilibili.com/msg/send'
            data = {
                'color': '16777215',
                'fontsize': '25',
                'mode': '1',
                'msg': msg,
                'rnd': str(int(time.time())),
                'roomid': room_id,
                'bubble': '0',
                'csrf_token': 'bc3ca64a45fc9ffe0982b5feba119bc1',
                'csrf': 'bc3ca64a45fc9ffe0982b5feba119bc1'
            }
            headers = {
                'cookie': "LIVE_BUVID=AUTO2716217597445981; _uuid=E57517E3-9B52-D19B-8B5A-6081CF0A2C3A49256infoc; buvid3=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp_plain=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(u)lukuYYJ~0J'uYkk))|kmJ; fingerprint=6fc5b3a08534cdd60c03bad6c6b13a83; SESSDATA=59e52819%2C1642557719%2Cd96be%2A71; bili_jct=543779f554e21b08eddb4d4cbdf660c1; DedeUserID=538828088; DedeUserID__ckMd5=f96ed607acbe97ad; sid=ii8aeooe; bp_t_offset_538828088=550125846804497333; _dfcaptcha=7e770e50e44b90f3f4ed8415b7d9cbe4; PVID=3LIVE_BUVID=AUTO2716217597445981; _uuid=E57517E3-9B52-D19B-8B5A-6081CF0A2C3A49256infoc; buvid3=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; buvid_fp_plain=4774D9E8-9613-4482-B998-662551DD6D2A13412infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(u)lukuYYJ~0J'uYkk))|kmJ; fingerprint=6fc5b3a08534cdd60c03bad6c6b13a83; SESSDATA=59e52819%2C1642557719%2Cd96be%2A71; bili_jct=543779f554e21b08eddb4d4cbdf660c1; DedeUserID=538828088; DedeUserID__ckMd5=f96ed607acbe97ad; sid=ii8aeooe; bp_t_offset_538828088=550125846804497333; _dfcaptcha=7e770e50e44b90f3f4ed8415b7d9cbe4; PVID=3",
                'origin': 'https://live.bilibili.com',
                'referer': 'https://live.bilibili.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
            }
            response = requests.post(url=url, data=data, headers=headers)
            resp_data = json.loads(response.text)
            if resp_data["code"] != 0:
                m = {
                    "group": 1014696092,
                    "text": response.text
                }
                self.msg_queue.append(m)
        
        send(21338446, 'uu和观众们该活动活动喝点水了哟')