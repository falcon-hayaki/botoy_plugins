from botoy import mark_recv, jconfig

if jconfig.get('youtube.api_key'):
    from utils.youtube_manager import YoutubeManager
    ym = YoutubeManager()

    from .ytbtimeline import ytbtimeline, ytbtimeline_subs
    from .get_ytb_video import get_ytb_video
    
    mark_recv(ytbtimeline)
    mark_recv(ytbtimeline_subs)
    mark_recv(get_ytb_video)