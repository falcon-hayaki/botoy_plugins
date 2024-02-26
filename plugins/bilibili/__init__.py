from botoy import mark_recv, jconfig

if jconfig.get('bilibili.cookie'):
    from utils.bili_manager import BiliManager
    bm = BiliManager()

    from .timeline import bili_dynamic_timeline
    
    mark_recv(bili_dynamic_timeline)