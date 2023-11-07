from botoy import mark_recv, jconfig

from .get_tweet import get_tweet

if jconfig.get('twitter'):
    from utils.twitter_manager import TwitterManager
    tm = TwitterManager()
    
    mark_recv(get_tweet)