import logging
import json
from typing import Dict, Optional, List, Any
from twikit import Client, Tweet, User
import twikit.tweet

# Monkey patch Tweet.__init__ to store raw data
_original_tweet_init = twikit.tweet.Tweet.__init__

def _patched_tweet_init(self, client: Client, data: Dict, user: User) -> None:
    _original_tweet_init(self, client, data, user)
    self.data = data
    self.legacy = data.get('legacy', {})
    self.created_at = self.legacy.get('created_at')

twikit.tweet.Tweet.__init__ = _patched_tweet_init


# Try to import botoy, but don't fail if it's not there, to allow standalone execution
try:
    from botoy import jconfig
except ImportError:
    jconfig = None

logger = logging.getLogger(__name__)

class TwikitManager:
    """
    A manager for interacting with Twitter (X) using the twikit library (v1.0.4 patched).
    This serves as an alternative to TwitterManager and XAPIManager.
    """

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initializes the TwikitManager.
        :param config: A dictionary with 'cookie' (string or dict).
                       If not provided, it will try to load from botoy's jconfig.
        """
        if config is None:
            if jconfig:
                self.config = jconfig.get_configuration('twitter')
            else:
                raise ValueError("A config dictionary must be provided when not running in a botoy environment.")
        else:
            self.config = config

        self.client = Client('en-US')
        
        cookie_input = self.config.get('cookie')
        if cookie_input:
            cookies = self._parse_cookie_input(cookie_input)
            # Twikit 1.0.4 uses requests.Session inside self.http.client
            if hasattr(self.client, 'http') and hasattr(self.client.http, 'client'):
                self.client.http.client.cookies.update(cookies)
            else:
                logger.warning("Could not set cookies: Client structure unexpected.")
        
        # Proxy support
        proxy = self.config.get('proxy')
        if proxy:
            # Twikit 1.0.4 uses requests, so we set proxies on the session
            if hasattr(self.client, 'http') and hasattr(self.client.http, 'client'):
                self.client.http.client.proxies.update({'http': proxy, 'https': proxy})

    def _parse_cookie_input(self, cookie_input: Any) -> Dict[str, str]:
        """Parses cookie string or dict into a dictionary for requests."""
        if isinstance(cookie_input, dict):
            return cookie_input
        
        cookies = {}
        if isinstance(cookie_input, str):
            pairs = cookie_input.split(';')
            for pair in pairs:
                if '=' in pair:
                    try:
                        key, value = pair.strip().split('=', 1)
                        cookies[key] = value
                    except ValueError:
                        continue
        return cookies

    # ------------------------ Synchronous Methods ------------------------

    def get_user_info(self, screen_name: str) -> Optional[Dict]:
        try:
            user = self.client.get_user_by_screen_name(screen_name)
            return self._parse_user(user)
        except Exception as e:
            logger.error(f"Error fetching user info for {screen_name}: {e}")
            return None

    def get_user_timeline(self, user_id: str, count: int = 20) -> Dict:
        try:
            # Twikit 1.0.4 returns Result[Tweet] which is iterable
            tweets_result = self.client.get_user_tweets(user_id, 'Tweets', count=count)
            # iterating tweets_result yields Tweet objects
            tweets = list(tweets_result)
            return self._parse_timeline_tweets(tweets)
        except Exception as e:
            logger.error(f"Error fetching timeline for {user_id}: {e}")
            return {}

    def get_tweet_detail(self, tweet_id: str) -> tuple[Optional[Dict], Optional[Dict]]:
        try:
            tweet = self.client.get_tweet_by_id(tweet_id)
            if tweet:
                return self._parse_tweet(tweet), self._parse_user(tweet.user)
            return None, None
        except Exception as e:
            logger.error(f"Error fetching tweet detail for {tweet_id}: {e}")
            return None, None

    # ------------------------ Parsers ------------------------

    def _parse_user(self, user: User) -> Dict:
        # User attributes in 1.0.4: id, name, screen_name, location, description, followers_count, following_count, profile_image_url
        return {
            'id': user.id,
            'name': user.name,
            'location': user.location if hasattr(user, 'location') else '',
            'description': user.description if hasattr(user, 'description') else '',
            'followers_count': user.followers_count,
            'following_count': user.following_count, 
            'icon': user.profile_image_url.replace('_normal', '') if hasattr(user, 'profile_image_url') else None
        }

    def _parse_timeline_tweets(self, tweets: List[Tweet]) -> Dict:
        timeline_data = {}
        if not tweets:
            return timeline_data
            
        for tweet in tweets:
            parsed_tweet = self._parse_tweet(tweet)
            if parsed_tweet:
                timeline_data[parsed_tweet['id']] = parsed_tweet
        return timeline_data

    def _parse_tweet(self, tweet: Tweet) -> Optional[Dict]:
        if not tweet:
            return None
        
        # Helper to parse legacy data
        def parse_legacy_data(legacy: Dict, user_info: Optional[Dict] = None) -> Dict:
            t_data = {
                'tweet_type': 'default',
                'id': legacy.get('id_str'),
                'text': legacy.get('full_text'),
                'created_at': legacy.get('created_at'),
                'imgs': [],
                'videos': []
            }
            
            # Media from extended_entities (better than entities)
            media = legacy.get('extended_entities', {}).get('media', [])
            if not media:
                media = legacy.get('entities', {}).get('media', [])
                
            for m in media:
                if m.get('type') == 'photo':
                    t_data['imgs'].append(m.get('media_url_https'))
                elif m.get('type') in ['video', 'animated_gif']:
                    video_info = m.get('video_info')
                    if video_info:
                        variants = video_info.get('variants', [])
                        mp4s = [v['url'] for v in variants if v.get('content_type') == 'video/mp4']
                        if mp4s:
                            # Simple logic: take the last one (usually highest quality) or sort
                            t_data['videos'].append(mp4s[-1])
            return t_data

    
        # Use patch self.data if available
        if hasattr(tweet, 'data'):
            legacy = tweet.data.get('legacy', {})
            # Main tweet data
            tweet_data = parse_legacy_data(legacy)
            
            # Check for retweet
            if 'retweeted_status_result' in legacy:
                tweet_data['tweet_type'] = 'retweet'
                rs_result = legacy['retweeted_status_result'].get('result', {})
                # Retrieve nested legacy and user
                if 'legacy' in rs_result:
                    rs_legacy = rs_result['legacy']
                    rs_user_res = rs_result.get('core', {}).get('user_results', {}).get('result', {})
                    # Need to parse user result to match _parse_user expected format
                    # But _parse_user expects User object.
                    # We can construct a dummy object or just parse dict manually.
                    rs_user_data = self._parse_user_dict(rs_user_res)
                    
                    tweet_data['retweet_data'] = {
                        'user_info': rs_user_data,
                        'data': parse_legacy_data(rs_legacy)
                    }
            
            # Check for quote
            elif 'quoted_status_result' in legacy:
                # Prioritize quote if present and not retweet
                tweet_data['tweet_type'] = 'quote'
                qs_result = legacy['quoted_status_result'].get('result', {})
                if 'legacy' in qs_result:
                    qs_legacy = qs_result['legacy']
                    qs_user_res = qs_result.get('core', {}).get('user_results', {}).get('result', {})
                    qs_user_data = self._parse_user_dict(qs_user_res)
                    
                    tweet_data['quote_data'] = {
                        'user_info': qs_user_data,
                        'data': parse_legacy_data(qs_legacy)
                    }

        else:
            # Fallback if no patch (minimal data)
            tweet_data = {
                'tweet_type': 'default',
                'id': tweet.id,
                'text': tweet.text,
                'created_at': getattr(tweet, 'created_at', None),
                'imgs': [],
                'videos': []
            }
            
        return tweet_data

    def _parse_user_dict(self, user_res: Dict) -> Dict:
        """Parses user result dict manually."""
        legacy = user_res.get('legacy', {})
        return {
            'id': user_res.get('rest_id'),
            'name': legacy.get('name'),
            'location': legacy.get('location', ''),
            'description': legacy.get('description', ''),
            'followers_count': legacy.get('followers_count'),
            'following_count': legacy.get('friends_count'),
            'icon': legacy.get('profile_image_url_https', '').replace('_normal', '') if legacy.get('profile_image_url_https') else None
        }

if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Try to load from botoy.json manually for testing
    config = None
    if os.path.exists('botoy.json'):
        try:
            with open('botoy.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = {
                    'cookie': data.get('twitter.cookie'),
                    # usage of proxy might be needed if you are in a region blocked by X
                    'proxy': data.get('twitter.proxy', 'http://127.0.0.1:7890') 
                }
                logger.info("Loaded config from botoy.json")
        except Exception as e:
            logger.error(f"Failed to load botoy.json: {e}")

    if not config or not config.get('cookie'):
        # Configure your test credentials here
        local_config = {
            "cookie": "ct0=bbbbc5ef336d1f0e36f65adb7c39dfac3b2902fb8347f438532e26c811773e3384814bd5f4aa9081c4d8c87daa8a7386a1ad0f2354ea31b141adcfd25f0e9de775b81c8ed3094b90a5d60f8fcec91e5f; auth_token=3cd56296a37ff4e8022b95a5ba63e3acd4873c12;", # ct0=...; auth_token=...
            "proxy": "http://127.0.0.1:7897"
        }
        config = local_config

    if not config.get('cookie') or 'your_cookie_string_here' in config.get('cookie'):
        logger.error("Please fill in your Twitter cookie in the `local_config` dictionary or ensure botoy.json exists.")
    else:
        tm = TwikitManager(config=config)
        
        logger.info("--- Testing get_user_info ---")
        user_name = "falcon_hayaki"
        user_info = tm.get_user_info(user_name)
        if user_info:
            logger.info(f"User Info: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
            
            logger.info("\n--- Testing get_user_timeline ---")
            timeline = tm.get_user_timeline(user_info['id'], count=5)
            logger.info(f"Timeline: Fetched {len(timeline)} tweets.")
            try:
                # timeline is dict {tweet_id: tweet_data}
                idx = 0
                for tid, tdata in timeline.items():
                    if idx >= 2: break
                    logger.info(f"Tweet {tid}: {json.dumps(tdata, indent=2, ensure_ascii=False)}")
                    idx += 1
            except Exception as e:
                logger.error(f"Error printing timeline: {e}")
                
            # Test detail
            if timeline:
                tid = list(timeline.keys())[0]
                logger.info(f"\n--- Testing get_tweet_detail for {tid} ---")
                detail, user = tm.get_tweet_detail(tid)
                logger.info(f"Detail: {json.dumps(detail, indent=2, ensure_ascii=False)}")
                logger.info(f"User: {json.dumps(user, indent=2, ensure_ascii=False)}")

            # Test detail for specific tweet
            specific_tid = "2022129158189723733"
            logger.info(f"\n--- Testing get_tweet_detail for specific ID {specific_tid} ---")
            spec_detail, spec_user = tm.get_tweet_detail(specific_tid)
            logger.info(f"Specific Detail: {json.dumps(spec_detail, indent=2, ensure_ascii=False)}")
            logger.info(f"Specific User: {json.dumps(spec_user, indent=2, ensure_ascii=False)}")
        else:
            logger.error("Failed to get user info.")
