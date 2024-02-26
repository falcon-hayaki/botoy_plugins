from botoy import mark_recv, jconfig

if jconfig.get('bilibili.cookie'):
    from utils.bili_manager import BiliManager
    bm = BiliManager()

    from .get_tweet import get_tweet
    from .timeline import timeline
    
    mark_recv(get_tweet)
    mark_recv(timeline)