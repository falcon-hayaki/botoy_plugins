__all__ = ["BilibiliApiManager"]

from typing import Optional, Dict, Any, List, Tuple
import asyncio
from datetime import datetime

from bilibili_api import Credential, video, user, dynamic, live
from botoy import jconfig


class BilibiliApiManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            bilibili_conf = jconfig.get_configuration("bilibili")
        else:
            bilibili_conf = config

        self.credential = Credential(
            sessdata=bilibili_conf.get("sessdata"),
            bili_jct=bilibili_conf.get("bili_jct"),
            buvid3=bilibili_conf.get("buvid3"),
            dedeuserid=bilibili_conf.get("dedeuserid"),
        )

    def get_user(self, uid: int) -> user.User:
        """Gets a User instance."""
        return user.User(uid=uid, credential=self.credential)
    
    async def get_user_info(self, user: user.User) -> Dict[str, Any]:
        """Gets a user's information."""
        return await user.get_user_info()
    
    async def get_user_relation(self, user: user.User) -> Dict[str, Any]:
        """Gets a user's relation information."""
        return await user.get_relation_info()
    
    async def get_dynamic_list(self, user: user.User, offset: str = "") -> Dict[str, Any]:
        """Gets a list of dynamics for a user."""
        return await user.get_dynamics_new(offset=offset)

    @staticmethod
    def parse_user_info(user_info: Dict[str, Any], relation: Dict[str, Any]) -> Dict[str, Any]:
        """Parses user information from API responses."""
        try:
            live_room = user_info.get("live_room", {}) or {}
            user_parsed = {
                "name": user_info.get("name"),
                "face": user_info.get("face"),
                "sign": user_info.get("sign"),
                "top_photo": user_info.get("top_photo"),
                "live_status": live_room.get("liveStatus"),
                "live_title": live_room.get("title"),
                "live_url": live_room.get("url"),
                "live_cover": live_room.get("cover"),
                "live_text": live_room.get("watched_show", {}).get("text_large"),
            }
            user_parsed.update(
                {
                    "followers": relation.get("follower"),
                    "following": relation.get("following"),
                }
            )
            return user_parsed
        except (KeyError, TypeError) as e:
            raise ValueError(
                f"Failed to parse user info: {e}, user_info: {user_info}, relation: {relation}"
            )

    @staticmethod
    def parse_timeline(timeline: Dict[str, Any]) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
        """Parses a timeline of dynamics."""
        try:
            dynamic_list_raw = timeline["items"]
            dynamic_id_list = []
            dynamic_data = {}
            for dr in dynamic_list_raw:
                dynamic_id, dynamic_parsed = BilibiliApiManager._parse_dynamic_one(dr)
                if dynamic_id and dynamic_parsed:
                    dynamic_id_list.append(dynamic_id)
                    dynamic_data[dynamic_id] = dynamic_parsed
            return dynamic_id_list, dynamic_data
        except (KeyError, TypeError) as e:
            raise ValueError(f"Failed to parse timeline: {e}, timeline: {timeline}")

    @staticmethod
    def _parse_dynamic_one(
        dynamic_raw: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Parses a single dynamic item."""
        if dynamic_raw.get("modules", {}).get("module_tag"):  # Skip pinned dynamics
            return None, None

        dynamic_id = dynamic_raw.get("id_str")
        if not dynamic_id:
            return None, None

        modules = dynamic_raw.get("modules", {})
        module_author = modules.get("module_author", {})
        pub_ts = module_author.get("pub_ts")
        public_time = datetime.fromtimestamp(int(pub_ts)) if pub_ts else None

        dynamic_parsed = {
            "text": (
                f"{module_author.get('name', '')}{module_author.get('pub_action', '发布于')}\n"
                f"{public_time.strftime('%Y-%m-%d %H:%M:%S%z') if public_time else ''}\n\n"
            ),
            "time": pub_ts,
            "imgs": [],
            "links": [dynamic_raw.get("basic", {}).get("jump_url", "")],
            "unknown_type": "",
        }

        dynamic_type = dynamic_raw.get("type")
        parser = BilibiliApiManager._get_dynamic_parser(dynamic_type)
        if parser:
            try:
                parser(dynamic_raw, dynamic_parsed)
            except (KeyError, TypeError):
                dynamic_parsed["unknown_type"] = dynamic_type
        elif dynamic_type in ["DYNAMIC_TYPE_LIVE_RCMD"]:
            return None, None
        else:
            dynamic_parsed["unknown_type"] = dynamic_type

        return dynamic_id, dynamic_parsed

    @staticmethod
    def _get_dynamic_parser(dynamic_type: str) -> Optional[callable]:
        """Returns the appropriate parser for a dynamic type."""
        parsers = {
            "DYNAMIC_TYPE_WORD": BilibiliApiManager._parse_word_dynamic,
            "DYNAMIC_TYPE_DRAW": BilibiliApiManager._parse_draw_dynamic,
            "DYNAMIC_TYPE_AV": BilibiliApiManager._parse_video_dynamic,
            "DYNAMIC_TYPE_FORWARD": BilibiliApiManager._parse_forward_dynamic,
            "DYNAMIC_TYPE_ARTICLE": BilibiliApiManager._parse_article_dynamic,
        }
        return parsers.get(dynamic_type)

    @staticmethod
    def _parse_word_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a word-only dynamic."""
        major = dynamic_raw.get("modules", {}).get("module_dynamic", {}).get("major", {})
        opus = major.get("opus", {})
        dynamic_parsed["text"] += opus.get("summary", {}).get("text", "") + "\n"

    @staticmethod
    def _parse_draw_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a draw dynamic."""
        major = dynamic_raw.get("modules", {}).get("module_dynamic", {}).get("major", {})
        opus = major.get("opus", {}) or {}
        dynamic_parsed["text"] += (opus.get("summary", {}) or {}).get("text", "") + "\n"
        dynamic_parsed["imgs"].extend([p.get("url") for p in opus.get("pics", []) if p.get("url")])

    @staticmethod
    def _parse_video_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a video dynamic."""
        major = dynamic_raw.get("modules", {}).get("module_dynamic", {}).get("major", {})
        archive = major.get("archive", {})
        dynamic_parsed["text"] += (
            f"链接：{archive.get('jump_url', '')}\n"
            f"标题：{archive.get('title', '')}\n"
            f"时长：{archive.get('duration_text', '')}\n"
            f"简介：{archive.get('desc', '')}\n"
        )
        if cover := archive.get("cover"):
            dynamic_parsed["imgs"].append(cover)

    @staticmethod
    def _parse_forward_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses a forward dynamic."""
        desc = dynamic_raw.get("modules", {}).get("module_dynamic", {}).get("desc", {})
        dynamic_parsed["text"] += (desc.get("text", "") or "") + "\n\n原动态: \n"

        orig = dynamic_raw.get("orig")
        if not orig:
            return

        _, orig_parsed = BilibiliApiManager._parse_dynamic_one(orig)
        if orig_parsed:
            if orig_parsed.get("unknown_type"):
                dynamic_parsed["text"] += f"未处理的类型：{orig_parsed['unknown_type']}"
            else:
                dynamic_parsed["text"] += orig_parsed.get("text", "")
                dynamic_parsed["imgs"].extend(orig_parsed.get("imgs", []))
                dynamic_parsed["links"].extend(orig_parsed.get("links", []))

    @staticmethod
    def _parse_article_dynamic(dynamic_raw: Dict[str, Any], dynamic_parsed: Dict[str, Any]):
        """Parses an article dynamic."""
        major = dynamic_raw.get("modules", {}).get("module_dynamic", {}).get("major", {})
        opus = major.get("opus", {})
        dynamic_parsed["text"] += (
            f"标题：{opus.get('title', '')}\n"
            f"摘要：{opus.get('summary', {}).get('text', '')}\n"
        )
        dynamic_parsed["imgs"].extend([p.get("url") for p in opus.get("pics", []) if p.get("url")])

    @staticmethod
    def parse_video_info(video_info_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Parses video information from an API response."""
        try:
            stat = video_info_raw.get("stat", {})
            return {
                "title": video_info_raw.get("title"),
                "pic": video_info_raw.get("pic"),
                "desc": video_info_raw.get("desc"),
                "pubdate": video_info_raw.get("pubdate"),
                "up": video_info_raw.get("owner", {}).get("name"),
                "view": stat.get("view"),
                "danmaku": stat.get("danmaku"),
                "reply": stat.get("reply"),
                "like": stat.get("like"),
                "favorite": stat.get("favorite"),
                "coin": stat.get("coin"),
                "share": stat.get("share"),
            }
        except (KeyError, TypeError) as e:
            raise ValueError(f"Failed to parse video info: {e}, video_info: {video_info_raw}")


if __name__ == "__main__":
    import json

    # It is recommended to enter the cookie into the configuration file,
    # and giving parameters is only for testing purposes.
    local_config = {
        "sessdata": "3dcb4364%2C1784989330%2C9d7b0%2A12CjBOyEbhx5cAYsmgGTLxRbwLDHPK-rsvD9GSQhaLgrP5HyuRXBbV03n7U3uF4mvoqo4SVllMb3BDLXZFVEFjMF9LNFVPc0dZTHF1bWRIWjg2Z2R6N2h6cnA2YjVUSmJfNUI1WDJSd3d2TzZ2Sm9JZnhfMFBxZVFMS2hiYzBIQ2VVajZqVFRMdzZ3IIE",
        "bili_jct": "7b849e6e8165d5961cbc45241a9aaaaa",
        "buvid3": "E33D5192-7863-A46C-6AAB-7803345C091530324infoc",
        "dedeuserid": "118970260",
    }
    bm = BilibiliApiManager(config=local_config)

    async def main():
        user = bm.get_user(910547)
        # user_info = await bm.get_user_info(user)
        # print(json.dumps(user_info, indent=4, ensure_ascii=False))
        # relation_info = await bm.get_user_relation(user)
        # print(json.dumps(relation_info, indent=4, ensure_ascii=False))

        dynamic_list = await bm.get_dynamic_list(user)
        with open("test_dynamic.json", "w") as f:
            json.dump(dynamic_list, f, ensure_ascii=False, indent=4)

        # user_info = await bm.get_user_info(1755331)
        # print(json.dumps(user_info, indent=4, ensure_ascii=False))

        # video_info = await bm.get_video_info("BV1Ufm4BCETh")
        # print(json.dumps(video_info, indent=4, ensure_ascii=False))
        
        # parsed_video_info = BilibiliApiManager.parse_video_info(video_info)
        # print(json.dumps(parsed_video_info, indent=4, ensure_ascii=False))


    asyncio.run(main())