from botoy import mark_recv, jconfig

if jconfig.get('twitter.cookie'):
    from utils.twitter_manager import TwitterManager
    tm = TwitterManager()

    from .get_tweet import get_tweet
    from .timeline import timeline
    
    mark_recv(get_tweet)
    mark_recv(timeline)