__all__ = ["BiliManager"]

import json
import random
import time
import urllib.parse
from datetime import datetime
from functools import reduce
from hashlib import md5
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from botoy import jconfig

Response = requests.Response


class BiliManager:
    def __init__(
        self,
        requests_get_fn: Optional[Callable[..., Response]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        :param requests_get_fn: A hook for the request function. Uses the requests library by default.
        :param config: A dict of config. Uses the jconfig library by default.
        """
        self.wbi = Wbi
        self._requests_get: Callable[..., Response] = requests.get
        if requests_get_fn:
            self.register_requests_hook(requests_get_fn)

        if config is None:
            bilibili_conf = jconfig.get_configuration('bilibili')
        else:
            bilibili_conf = config
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Cookie': bilibili_conf.get('cookie', ''),
        }
        self.last_request_time = 0

    def register_requests_hook(self, requests_get_fn: Callable[..., Response]) -> None:
        """Registers a hook for the request function."""
        self._requests_get = requests_get_fn

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Response:
        now = time.time()
        cooldown = random.uniform(1, 1.5)
        if now - self.last_request_time < cooldown:
            sleep_time = cooldown - (now - self.last_request_time)
            time.sleep(sleep_time)

        response = self._requests_get(url, headers=self.headers, params=params)
        self.last_request_time = time.time()
        return response

    def get_nav(self) -> Response:
        """Gets navigation information."""
        return self._get('https://api.bilibili.com/x/web-interface/nav')

    def get_live_info(self, room_id: int) -> Response:
        """Gets live room information."""
        return self._get(f'https://api.live.bilibili.com/room/v1/Room/get_info?id={room_id}')

    def get_video_info(self, bvid: str) -> Response:
        """Gets video information."""
        return self._get(f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}')

    def get_dynamic_list(self, uid: int) -> Response:
        """Gets a list of dynamics for a user."""
        params = {
            'host_mid': uid,
            'offset': '',
            'timezone_offset': -480,
            'platform': 'web',
            'features': 'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote',
            'web_location': '333.999',
        }
        return self._get('https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space', params=params)

    def get_user_card(self, uid: int) -> Response:
        """
        NOTE: 易被风控已弃用
        Gets a user's card information.
        """
        return self._get(f'https://api.bilibili.com/x/web-interface/card?mid={uid}')
    
    def get_user_relation(self, uid: int) -> Response:
        """Gets a user's relation information."""
        return self._get(f'https://api.bilibili.com/x/relation/stat?vmid={uid}')

    def get_user_info(self, uid: int) -> Response:
        """Gets a user's information with WBI signature."""
        try:
            img_key, sub_key = self.wbi.get_wbi_keys(self.get_nav())
            signed_params = self.wbi.enc_wbi(params={'mid': uid}, img_key=img_key, sub_key=sub_key)
            url = f'https://api.bilibili.com/x/space/wbi/acc/info?{urllib.parse.urlencode(signed_params)}'
            return self._get(url)
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to get WBI keys: {e}")

    @staticmethod
    def parse_user_info(user_info: Dict[str, Any], relation: Dict[str, Any]) -> Dict[str, Any]:
        """Parses user information from API responses."""
        try:
            user_data = user_info['data']
            live_room = user_data.get('live_room', {}) or {}
            user_parsed = {
                'name': user_data.get('name'),
                'face': user_data.get('face'),
                'sign': user_data.get('sign'),
                'top_photo': user_data.get('top_photo'),
                'live_status': live_room.get('liveStatus'),
                'live_title': live_room.get('title'),
                'live_url': live_room.get('url'),
                'live_cover': live_room.get('cover'),
                'live_text': live_room.get('watched_show', {}).get('text_large'),
            }

            relation_data = relation['data']
            user_parsed.update({
                'followers': relation_data.get('follower'),
                'following': relation_data.get('following'),
            })
            return user_parsed
        except (KeyError, TypeError) as e:
            raise ValueError(f"Failed to parse user info: {e}, user_info: {user_info}, relation: {relation}")
    @staticmethod
    def parse_timeline(timeline: Dict[str, Any]) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
        """Parses a timeline of dynamics."""
        try:
            dynamic_list_raw = timeline['data']['items']
            dynamic_id_list = []
            dynamic_data = {}
            for dr in dynamic_list_raw:
                dynamic_id, dynamic_parsed = BiliManager._parse_dynamic_one(dr)
                if dynamic_id and dynamic_parsed:
                    dynamic_id_list.append(dynamic_id)
                    dynamic_data[dynamic_id] = dynamic_parsed
            return dynamic_id_list, dynamic_data
        except (KeyError, TypeError) as e:
            raise ValueError(f"Failed to parse timeline: {e}, timeline: {timeline}")

    @staticmethod
    def _parse_dynamic_one(dynamic_raw: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Parses a single dynamic item."""
        if dynamic_raw.get('modules', {}).get('module_tag'):  # Skip pinned dynamics
            return None, None

        dynamic_id = dynamic_raw.get('id_str')
        if not dynamic_id:
            return None, None

        modules = dynamic_raw.get('modules', {})
        module_author = modules.get('module_author', {})
        pub_ts = module_author.get('pub_ts')
        public_time = datetime.fromtimestamp(int(pub_ts)) if pub_ts else None

        dynamic_parsed = {
            'text': (
                f"{module_author.get('name', '')}{module_author.get('pub_action', '发布于')}\n"
                f"{public_time.strftime('%Y-%m-%d %H:%M:%S%z') if public_time else ''}\n\n"
            ),
            'time': pub_ts,
            'imgs': [],
            'links': [dynamic_raw.get('basic', {}).get('jump_url', '')],
            'unknown_type': '',
        }

        dynamic_type = dynamic_raw.get('type')
        parser = BiliManager._get_dynamic_parser(dynamic_type)
        if parser:
            try:
                parser(dynamic_raw, dynamic_parsed)
            except (KeyError, TypeError):
                dynamic_parsed['unknown_type'] = dynamic_type
        elif dynamic_type in ['DYNAMIC_TYPE_LIVE_RCMD']:
            return None, None
        else:
            dynamic_parsed['unknown_type'] = dynamic_type

        return dynamic_id, dynamic_parsed

    @staticmethod
    def _get_dynamic_parser(dynamic_type: str) -> Optional[Callable]:
        """Returns the appropriate parser for a dynamic type."""
        parsers = {
            'DYNAMIC_TYPE_WORD': BiliManager._parse_word_dynamic,
            'DYNAMIC_TYPE_DRAW': BiliManager._parse_draw_dynamic,
            'DYNAMIC_TYPE_AV': BiliManager._parse_video_dynamic,
            'DYNAMIC_TYPE_FORWARD': BiliManager._parse_forward_dynamic,
            'DYNAMIC_TYPE_ARTICLE': BiliManager._parse_article_dynamic,
        }
        return parsers.get(dynamic_type)

    @staticmethod
    def _parse_word_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a word-only dynamic."""
        major = dynamic_raw.get('modules', {}).get('module_dynamic', {}).get('major', {})
        opus = major.get('opus', {})
        dynamic_parsed['text'] += opus.get('summary', {}).get('text', '') + '\n'

    @staticmethod
    def _parse_draw_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a draw dynamic."""
        major = dynamic_raw.get('modules', {}).get('module_dynamic', {}).get('major', {})
        opus = major.get('opus', {}) or {}
        dynamic_parsed['text'] += (opus.get('summary', {}) or {}).get('text', '') + '\n'
        dynamic_parsed['imgs'].extend([p.get('url') for p in opus.get('pics', []) if p.get('url')])

    @staticmethod
    def _parse_video_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a video dynamic."""
        major = dynamic_raw.get('modules', {}).get('module_dynamic', {}).get('major', {})
        archive = major.get('archive', {})
        dynamic_parsed['text'] += (
            f"链接：{archive.get('jump_url', '')}\n"
            f"标题：{archive.get('title', '')}\n"
            f"时长：{archive.get('duration_text', '')}\n"
            f"简介：{archive.get('desc', '')}\n"
        )
        if cover := archive.get('cover'):
            dynamic_parsed['imgs'].append(cover)

    @staticmethod
    def _parse_forward_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a forward dynamic."""
        desc = dynamic_raw.get('modules', {}).get('module_dynamic', {}).get('desc', {})
        dynamic_parsed['text'] += (desc.get('text', '') or '') + '\n\n原动态: \n'

        orig = dynamic_raw.get('orig')
        if not orig:
            return

        _, orig_parsed = BiliManager._parse_dynamic_one(orig)
        if orig_parsed:
            if orig_parsed.get('unknown_type'):
                dynamic_parsed['text'] += f"未处理的类型：{orig_parsed['unknown_type']}"
            else:
                dynamic_parsed['text'] += orig_parsed.get('text', '')
                dynamic_parsed['imgs'].extend(orig_parsed.get('imgs', []))
                dynamic_parsed['links'].extend(orig_parsed.get('links', []))

    @staticmethod
    def _parse_article_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses an article dynamic."""
        major = dynamic_raw.get('modules', {}).get('module_dynamic', {}).get('major', {})
        opus = major.get('opus', {})
        dynamic_parsed['text'] += (
            f"标题：{opus.get('title', '')}\n"
            f"摘要：{opus.get('summary', {}).get('text', '')}\n"
        )
        dynamic_parsed['imgs'].extend([p.get('url') for p in opus.get('pics', []) if p.get('url')])

    @staticmethod
    def parse_video_info(video_info_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Parses video information from an API response."""
        try:
            video_res = video_info_raw['data']
            stat = video_res.get('stat', {})
            return {
                'title': video_res.get('title'),
                'pic': video_res.get('pic'),
                'desc': video_res.get('desc'),
                'pubdate': video_res.get('pubdate'),
                'up': video_res.get('owner', {}).get('name'),
                'view': stat.get('view'),
                'danmaku': stat.get('danmaku'),
                'reply': stat.get('reply'),
                'like': stat.get('like'),
                'favorite': stat.get('favorite'),
                'coin': stat.get('coin'),
                'share': stat.get('share'),
            }
        except (KeyError, TypeError) as e:
            raise ValueError(f"Failed to parse video info: {e}, video_info: {video_info_raw}")


class Wbi:
    """
    WBI signature.
    https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/misc/sign/wbi.md
    """
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]

    @classmethod
    def get_mixin_key(cls, orig: str) -> str:
        """Disrupt the order of characters in imgKey and subKey for encoding."""
        return reduce(lambda s, i: s + orig[i], cls.MIXIN_KEY_ENC_TAB, '')[:32]

    @classmethod
    def enc_wbi(cls, params: Dict[str, Any], img_key: str, sub_key: str) -> Dict[str, Any]:
        """Sign the request parameters with WBI."""
        mixin_key = cls.get_mixin_key(img_key + sub_key)
        curr_time = round(time.time())
        params['wts'] = curr_time
        params = dict(sorted(params.items()))
        
        # Filter out "!'()*" characters from values
        params = {
            k: ''.join(filter(lambda char: char not in "!'()", str(v)))
            for k, v in params.items()
        }
        
        query = urllib.parse.urlencode(params)
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()
        params['w_rid'] = wbi_sign
        return params

    @staticmethod
    def get_wbi_keys(nav_resp: Response) -> Tuple[str, str]:
        """Get the latest img_key and sub_key."""
        json_content = nav_resp.json()
        img_url: str = json_content['data']['wbi_img']['img_url']
        sub_url: str = json_content['data']['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        return img_key, sub_key

if __name__ == '__main__':
    # a dict of config
    local_config = {
        'cookie': "enable_web_push=DISABLE; home_feed_column=5; browser_resolution=1435-709; buvid_fp=841242c671d7759bb558ab9dfa5163cd; buvid4=1BC7EA8A-2AFD-CA80-C581-B53F0A335B9782428-024081417-ikIgcXCMkzfSQ2SmdyYClw%3D%3D; SESSDATA=0389d879%2C1781275344%2C46fa3%2Ac2CjCiQfqy4LxUkqPGDZ4eQbukM8KmZve2XINEw7cP5196Jjxc7b8YfoeiB0PlVRo6YhoSVnJTVWRmRjlZTlJDYVVIUmlHcm1NWUFoaVpFUFBvZTRQZHZGNVpQYlhmbE03TVFOQ1I5Y1NQZXM4WEFkMjVCUE9SN0FsV29sMnNyb1ZXUEhIOTRtb0ZnIIEC; bili_jct=e426c36e3dc23d99e0206875cb13ffc7; DedeUserID=118970260; DedeUserID__ckMd5=6c0f45d7b2cdbe8d; bp_t_offset_118970260=1146448095538577408; CURRENT_FNVAL=4048; header_theme_version=OPEN; PVID=2; fingerprint=77b1f389623c9f9e573cbcf54e958fe7; buvid_fp_plain=undefined; CURRENT_QUALITY=80; enable_feed_channel=ENABLE; dy_spec_agreed=1; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; buvid3=E33D5192-7863-A46C-6AAB-7803345C091530324infoc; b_nut=1755302130; _uuid=EC956FE3-C9C9-4362-AB19-1021DF364FBCA31356infoc; hit-dyn-v2=1; theme-switch-show=SHOWED; LIVE_BUVID=AUTO4717649425309845; rpdid=0zbfVG8FSO|YSNDmlG5|4DU|3w1VryQt; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjU5NzAwNTksImlhdCI6MTc2NTcxMDc5OSwicGx0IjotMX0.IZ-f6e8GfLphql52BASD_tH-apL4XaVmylfQt7rz4o8; bili_ticket_expires=1765969999; b_lsid=C9D85CCA_19B1FE20CED; timeMachine=0"
    }
    bm = BiliManager(config=local_config)
    # print(bm.get_live_info(591194).json())
    # print(bm.get_dynamic_list(1755331).json())
    with open('test.json', 'w') as f:
        json.dump(bm.get_dynamic_list(1755331).json(), f, ensure_ascii=False)
    # print(bm.get_user_info(1755331).json())
    # print(bm.get_user_card(1755331).json())
    # print(bm.get_video_info('BV1Ufm4BCETh').json())
