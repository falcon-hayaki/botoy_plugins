from botoy import mark_recv, jconfig

if jconfig.get('twitter'):
    from utils.twitter_manager import TwitterManager
    tm = TwitterManager()
    
    