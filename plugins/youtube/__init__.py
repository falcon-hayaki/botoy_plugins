from botoy import mark_recv, jconfig

if jconfig.get('youtube.api_key'):
    from utils.youtube_manager import YoutubeManager
    ym = YoutubeManager()

    from .ytbtimeline import ytbtimeline
    
    mark_recv(ytbtimeline)