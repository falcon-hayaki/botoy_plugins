import requests
import json
from functools import reduce
from hashlib import md5
import urllib.parse
import time
from datetime import datetime

from botoy import jconfig

class BiliManager():
    def __init__(self, requests_get_fn=None) -> None:
        '''
        :param requests_hook: request请求时调用函数的钩子。不传入时使用requests标准库请求
        '''
        self.wbi = Wbi
        self.__requests_get = requests.get
        if requests_get_fn is not None:
            self.register_requests_hook(requests_get_fn)
            
        # get config
        bilibili_conf = jconfig.get_configuration('bilibili')
        # init headers
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Cookie': bilibili_conf.get('cookie')
        }
            
    def register_requests_hook(self, requests_get_fn):
        '''
        注册request请求时调用函数的钩子
        '''
        self.__requests_get = requests_get_fn
    
    def __get(self, url, params=None):
        return self.__requests_get(url, headers=self.headers, params=params)
    
    def get_nav(self):
        url = 'https://api.bilibili.com/x/web-interface/nav'
        return self.__get(url)
    
    def get_live_info(self, room_id):
        url = f'https://api.live.bilibili.com/room/v1/Room/get_info?id={room_id}'
        return self.__get(url)
    
    def get_video_info(self, bvid):
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        return self.__get(url)
    
    def get_dynamic_list(self, uid):
        url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?offset=&host_mid={uid}&timezone_offset=-480&platform=web&features=itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote&web_location=333.999'
        return self.__get(url)
    
    def get_user_card(self, uid):
        url = f'https://api.bilibili.com/x/web-interface/card?mid={uid}'
        return self.__get(url)
    
    def get_user_info(self, uid):
        img_key, sub_key = self.wbi.getWbiKeys(self.get_nav())
        signed_params = self.wbi.encWbi(
            params={
                'mid': uid
            },
            img_key=img_key,
            sub_key=sub_key
        )
        url = f'https://api.bilibili.com/x/space/wbi/acc/info?{urllib.parse.urlencode(signed_params)}'
        return self.__get(url)
    
    # ------------------------ 解析返回json ------------------------
    @staticmethod
    def parse_user_info(user_info, user_card):
        try:
            user_result = user_info['data']
            user_parsed = dict(
                name=user_result['name'],
                face=user_result['face'],
                sign=user_result['sign'],
                top_photo=user_result['top_photo'],
                live_status=(user_result.get('live_room') or {}).get('liveStatus'),
                live_title=(user_result.get('live_room') or {}).get('title'),
                live_url=(user_result.get('live_room') or {}).get('url'),
                live_cover=(user_result.get('live_room') or {}).get('cover'),
                live_text=(user_result.get('live_room') or {}).get('watched_show', {}).get('text_large'),
            )
            user_result = user_card['data']
            user_parsed.update(dict(
                followers=user_result['follower'],
                following=user_result['card']['attention'],
            ))
            return user_parsed
        except:
            raise ValueError(f'user_info: {user_info}')
        
    @staticmethod
    def parse_timeline(timeline):
        try:
            dynamic_list_raw = timeline['data']['items']
            dynamic_id_list = []
            dynamic_data = {}
            for dr in dynamic_list_raw:
                dynamic_id, dynamic_parsed = BiliManager.parse_dynamic_one(dr)
                if dynamic_id:
                    dynamic_id_list.append(dynamic_id)
                    dynamic_data[dynamic_id] = dynamic_parsed
        except:
            raise ValueError(f'timeline: {timeline}')
        return dynamic_id_list, dynamic_data
            
    @staticmethod
    def parse_dynamic_one(dynamic_raw):
        '''
        https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/dynamic/all.md#%E8%8E%B7%E5%8F%96%E5%8A%A8%E6%80%81%E5%88%97%E8%A1%A8
        '''
        
        # 跳过置顶
        modules = dynamic_raw.get('modules', {})
        if modules.get('module_tag'):
            return None, None
        
        dynamic_id = dynamic_raw['id_str']
        dynamic_parsed = {
            'text': '',
            'time': None,
            'imgs': [],
            'links': [],
            'unknown_type': ''
        }
        # NOTE: 公共部分
        basic = dynamic_raw.get('basic', {})
        module_author = modules.get('module_author', {})
        public_time = datetime.fromtimestamp(module_author.get('pub_ts'))
        dynamic_parsed['time'] = module_author.get('pub_ts')
        dynamic_parsed['text'] += f"{module_author.get('name')}{module_author.get('pub_action') or '发布于'}\n{public_time.strftime('%Y-%m-%d %H:%M:%S%z')}\n\n"
        dynamic_parsed['links'].append(basic.get('jump_url', ''))
        # NOTE: 分类处理
        dynamic_type = dynamic_raw['type']
        module_dynamic = modules.get('module_dynamic', {})
        # 纯文字动态
        if dynamic_type in ['DYNAMIC_TYPE_WORD', 'DYNAMIC_TYPE_DRAW']:
            major = module_dynamic.get('major', {})
            opus = major.get('opus', {})
            dynamic_parsed['text'] += opus.get('summary', {}).get('text', '') + '\n'
            dynamic_parsed['imgs'] = [p.get('url') for p in opus.get('pics')]
        # 视频动态
        elif dynamic_type == 'DYNAMIC_TYPE_AV':
            major = module_dynamic.get('major', {})
            archive = major.get('archive', {})
            dynamic_parsed['text'] += f"链接：{archive.get('jump_url', '')}\n"
            dynamic_parsed['text'] += f"标题：{archive.get('title', '')}\n"
            dynamic_parsed['text'] += f"时长：{archive.get('duration_text', '')}\n"
            dynamic_parsed['text'] += f"简介：{archive.get('desc', '')}\n"
            if cover := archive.get('cover'):
                dynamic_parsed['imgs'].append(cover)
        # 转发动态
        elif dynamic_type == 'DYNAMIC_TYPE_FORWARD':
            desc = module_dynamic.get('desc', {})
            dynamic_parsed['text'] += desc.get('text', '') + '\n\n'
            dynamic_parsed['text'] += '原动态: \n'
            orig = dynamic_raw.get('orig', {})
            orig_id, orig_parsed = BiliManager.parse_dynamic_one(orig)
            if orig_parsed['unknown_type']:
                dynamic_parsed['text'] += f"未处理的类型：{orig_parsed['unknown_type']}"
            else:
                dynamic_parsed['text'] += orig_parsed['text']
                dynamic_parsed['imgs'] += orig_parsed['imgs']
                dynamic_parsed['links'] += orig_parsed['links']
        # 不作处理的动态
        ## 直播动态
        elif dynamic_type in ['DYNAMIC_TYPE_LIVE_RCMD']:
            return None, None
        # 其它动态
        else:
            dynamic_parsed['unknown_type'] = dynamic_type
        
        return dynamic_id, dynamic_parsed
    
    @staticmethod
    def parse_video_info(video_info_raw):
        try:
            video_res = video_info_raw['data']
            return dict(
                title=video_res['title'],
                pic=video_res['pic'],
                desc=video_res['desc'],
                pubdate=video_res['pubdate'],
                up=video_res['owner']['name'],
                view=video_res['stat']['view'],
                danmaku=video_res['stat']['danmaku'],
                reply=video_res['stat']['reply'],
                like=video_res['stat']['like'],
                favorite=video_res['stat']['favorite'],
                coin=video_res['stat']['coin'],
                share=video_res['stat']['share'],
            )
        except:
            raise ValueError(f'video_info: {video_info_raw}')
    
class Wbi():
    '''
    WBI签名。
    https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/misc/sign/wbi.md
    '''
    mixinKeyEncTab = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]

    @classmethod
    def getMixinKey(cls, orig: str):
        '对 imgKey 和 subKey 进行字符顺序打乱编码'
        return reduce(lambda s, i: s + orig[i], cls.mixinKeyEncTab, '')[:32]

    @classmethod
    def encWbi(cls, params: dict, img_key: str, sub_key: str):
        '为请求参数进行 wbi 签名'
        mixin_key = cls.getMixinKey(img_key + sub_key)
        curr_time = round(time.time())
        params['wts'] = curr_time                                   # 添加 wts 字段
        params = dict(sorted(params.items()))                       # 按照 key 重排参数
        # 过滤 value 中的 "!'()*" 字符
        params = {
            k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
            for k, v 
            in params.items()
        }
        query = urllib.parse.urlencode(params)                      # 序列化参数
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()    # 计算 w_rid
        params['w_rid'] = wbi_sign
        return params

    @staticmethod
    def getWbiKeys(nav_resp):
        '获取最新的 img_key 和 sub_key'
        json_content = nav_resp.json()
        img_url: str = json_content['data']['wbi_img']['img_url']
        sub_url: str = json_content['data']['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        return img_key, sub_key
    
if __name__ == '__main__':
    bm = BiliManager()
    # print(bm.get_live_info(591194).json())
    print(bm.get_dynamic_list(686647628).json())
    # with open('test.json', 'w') as f:
    #     json.dump(bm.get_dynamic_list(3546626599684797).json(), f)
    # print(bm.get_user_info(3546626599684797).json())
    # print(bm.get_user_card(3546626599684797).json())
    # print(bm.get_video_info('BV1aw411X7hx').json())