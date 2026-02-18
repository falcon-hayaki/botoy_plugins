from botoy import mark_recv, jconfig

if jconfig.get('twitter.cookie'):
    from utils.twitter_manager import TwitterManager
    tm = TwitterManager()

    from .get_tweet import get_tweet
    from .timeline import timeline
    
    # mark_recv(get_tweet)
    # mark_recv(timeline)

    # Twikit implementation (Alternative)
    # from .get_tweet_by_twikit import get_tweet_by_twikit
    # from .timeline_by_twikit import timeline_by_twikit
    # mark_recv(get_tweet_by_twikit)
    # mark_recv(timeline_by_twikit)

if jconfig.get('x_api.bearer_token'):
    from utils.x_api_manager import XAPIManager
    xm = XAPIManager()
    
    from .get_tweet_withxapi import get_tweet_withxapi
    from .timeline_withxapi import timeline_withxapi
    from .get_xapi_usage import get_xapi_usage
    
    # mark_recv(get_tweet_withxapi)
    # mark_recv(timeline_withxapi)
    # mark_recv(get_xapi_usage)