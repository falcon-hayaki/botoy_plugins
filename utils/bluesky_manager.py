from pydantic import BaseModel, HttpUrl
from typing import Union, Optional
from datetime import datetime
import json
import traceback
from typing import List

from atproto import Client

# -------------------------- Models --------------------------
class TextContent(BaseModel):
    text: str

class ImageContent(BaseModel):
    image_url: HttpUrl

class VideoContent(BaseModel):
    video_url: HttpUrl
    duration: int

class Post(BaseModel):
    post_id: int
    content: Union[TextContent, ImageContent, VideoContent]
    created_at: datetime
    post_type: str
    self_type: str
    parent_post: Optional['Post'] = None
    root_post: Optional['Post'] = None

    class Config:
        arbitrary_types_allowed = True


# -------------------------- Manager --------------------------
class BlueskyManager():
    def __init__(self):
        self.client = Client()
        self.client.login('hayaki.icu', 'falcon19980311')

    def get_user_profile(self, handle: str):
        profile = self.client.get_profile(actor=handle)
        return profile
    
    def get_user_timeline(self, did):
        data = self.client.get_author_feed(actor=did)
        return self.serialise_resp(data)
    
    def parse_timeline(self, timeline_data) -> dict:
        try:
            data: List[Post] = []
            for post_data in timeline_data['feed']:
                
            return {
                'completed': True,
                'data': data
            }
        except:
            return {
                'completed': False,
                'data': str(traceback.format_exc())
            }
    
    @classmethod
    def serialise_resp(cls, obj):
        try:
            if isinstance(obj, (int, float, str, bool)):
                return obj
            return json.dumps(obj)
        except:
            try:
                return {
                    str(k): cls.serialise_resp(v)
                    for k, v in dict(obj).items()
                }
            except:
                try:
                    return [
                        cls.serialise_resp(o)
                        for o in (list(obj))
                    ]
                except:
                    try:
                        return str(obj)
                    except:
                        return obj.__name__

if __name__ == '__main__':
    bm = BlueskyManager()
    user_profile = bm.get_user_profile('momoshiki.bsky.social')
    # print(dict(user_profile))
    did = user_profile.did
    
    timeline_data = bm.get_user_timeline(did)
    serializable_dict = bm.serialise_resp(timeline_data)
    with open('test.json', 'w') as f:
        json.dump(serializable_dict, f, ensure_ascii=False, indent=4)