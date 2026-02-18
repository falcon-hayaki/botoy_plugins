import logging
import json
import asyncio
from typing import Dict, Optional, List, Any
from twikit import Client

# Try to import botoy, but don't fail if it's not there, to allow standalone execution
try:
    from botoy import jconfig
except ImportError:
    jconfig = None

logger = logging.getLogger(__name__)


class TwikitManager:
    """
    A manager for interacting with Twitter (X) using the twikit library (v2.x).
    All methods are async. This serves as an alternative to TwitterManager and XAPIManager.
    """

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initializes the TwikitManager.
        :param config: A dictionary with 'cookie' (string or dict) and optional 'proxy'.
                       If not provided, it will try to load from botoy's jconfig.
        """
        if config is None:
            if jconfig:
                self.config = jconfig.get_configuration('twitter')
            else:
                raise ValueError("A config dictionary must be provided when not running in a botoy environment.")
        else:
            self.config = config

        proxy = self.config.get('proxy')
        self.client = Client(language='en-US', proxy=proxy)

        cookie_input = self.config.get('cookie')
        if cookie_input:
            cookies = self._parse_cookie_input(cookie_input)
            self.client.set_cookies(cookies)

    def _parse_cookie_input(self, cookie_input: Any) -> Dict[str, str]:
        """Parses cookie string or dict into a dictionary."""
        if isinstance(cookie_input, dict):
            return cookie_input

        cookies = {}
        if isinstance(cookie_input, str):
            for pair in cookie_input.split(';'):
                if '=' in pair:
                    try:
                        key, value = pair.strip().split('=', 1)
                        cookies[key.strip()] = value.strip()
                    except ValueError:
                        continue
        return cookies

    # ------------------------ Async Methods ------------------------

    async def get_user_info(self, screen_name: str) -> Optional[Dict]:
        try:
            user = await self.client.get_user_by_screen_name(screen_name)
            return self._parse_user(user)
        except Exception as e:
            logger.error(f"Error fetching user info for {screen_name}: {e}")
            return None

    async def get_user_timeline(self, user_id: str, count: int = 20) -> Dict:
        try:
            tweets_result = await self.client.get_user_tweets(user_id, 'Tweets', count=count)
            tweets = list(tweets_result)
            return self._parse_timeline_tweets(tweets)
        except Exception as e:
            logger.error(f"Error fetching timeline for {user_id}: {e}")
            return {}

    async def get_tweet_detail(self, tweet_id: str) -> tuple[Optional[Dict], Optional[Dict]]:
        try:
            tweet = await self.client.get_tweet_by_id(tweet_id)
            if tweet:
                return self._parse_tweet(tweet), self._parse_user(tweet.user)
            return None, None
        except Exception as e:
            logger.error(f"Error fetching tweet detail for {tweet_id}: {e}")
            return None, None

    # ------------------------ Parsers ------------------------

    def _parse_user(self, user) -> Dict:
        return {
            'id': user.id,
            'name': user.name,
            'screen_name': user.screen_name,
            'location': getattr(user, 'location', '') or '',
            'description': getattr(user, 'description', '') or '',
            'followers_count': getattr(user, 'followers_count', 0),
            'following_count': getattr(user, 'following_count', 0),
            'icon': (user.profile_image_url or '').replace('_normal', '') if getattr(user, 'profile_image_url', None) else None,
        }

    def _parse_timeline_tweets(self, tweets) -> Dict:
        timeline_data = {}
        for tweet in tweets:
            parsed = self._parse_tweet(tweet)
            if parsed and parsed.get('id'):
                timeline_data[parsed['id']] = parsed
        return timeline_data

    def _parse_tweet(self, tweet) -> Optional[Dict]:
        if not tweet:
            return None

        tweet_data = {
            'tweet_type': 'default',
            'id': tweet.id,
            'text': tweet.text,
            'created_at': tweet.created_at,
            'imgs': [],
            'videos': [],
        }

        # Parse media from tweet.media (list of Photo/Video/AnimatedGif objects)
        for m in (tweet.media or []):
            media_type = getattr(m, 'type', '')
            if media_type == 'photo':
                url = getattr(m, 'media_url', None)
                if url:
                    tweet_data['imgs'].append(url)
            elif media_type in ('video', 'animated_gif'):
                streams = getattr(m, 'streams', None)
                if streams:
                    # streams is a list of Stream objects; pick highest bitrate mp4
                    mp4_streams = [s for s in streams if getattr(s, 'content_type', '') == 'video/mp4']
                    if mp4_streams:
                        best = max(mp4_streams, key=lambda s: getattr(s, 'bitrate', 0) or 0)
                        url = getattr(best, 'url', None)
                        if url:
                            tweet_data['videos'].append(url)

        # Check for retweet
        retweeted = getattr(tweet, 'retweeted_tweet', None)
        if retweeted:
            tweet_data['tweet_type'] = 'retweet'
            rt_parsed = self._parse_tweet(retweeted)
            rt_user = self._parse_user(retweeted.user) if getattr(retweeted, 'user', None) else {}
            tweet_data['retweet_data'] = {
                'user_info': rt_user,
                'data': rt_parsed or {},
            }
        else:
            # Check for quote
            quoted = getattr(tweet, 'quote', None)
            if quoted:
                tweet_data['tweet_type'] = 'quote'
                q_parsed = self._parse_tweet(quoted)
                q_user = self._parse_user(quoted.user) if getattr(quoted, 'user', None) else {}
                tweet_data['quote_data'] = {
                    'user_info': q_user,
                    'data': q_parsed or {},
                }

        return tweet_data


if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    config = None
    if os.path.exists('botoy.json'):
        try:
            with open('botoy.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = {
                    'cookie': data.get('twitter.cookie'),
                    'proxy': data.get('twitter.proxy', 'http://127.0.0.1:7890')
                }
                logger.info("Loaded config from botoy.json")
        except Exception as e:
            logger.error(f"Failed to load botoy.json: {e}")

    if not config or not config.get('cookie'):
        local_config = {
            "cookie": "ct0=YOUR_CT0; auth_token=YOUR_AUTH_TOKEN;",
            "proxy": "http://127.0.0.1:7897"
        }
        config = local_config

    async def main():
        tm = TwikitManager(config=config)

        logger.info("--- Testing get_user_info ---")
        user_info = await tm.get_user_info("falcon_hayaki")
        if user_info:
            logger.info(f"User Info: {json.dumps(user_info, indent=2, ensure_ascii=False)}")

            logger.info("\n--- Testing get_user_timeline ---")
            timeline = await tm.get_user_timeline(user_info['id'], count=5)
            logger.info(f"Timeline: Fetched {len(timeline)} tweets.")
            for i, (tid, tdata) in enumerate(timeline.items()):
                if i >= 2:
                    break
                logger.info(f"Tweet {tid}: {json.dumps(tdata, indent=2, ensure_ascii=False)}")

            if timeline:
                tid = list(timeline.keys())[0]
                logger.info(f"\n--- Testing get_tweet_detail for {tid} ---")
                detail, user = await tm.get_tweet_detail(tid)
                logger.info(f"Detail: {json.dumps(detail, indent=2, ensure_ascii=False)}")
                logger.info(f"User: {json.dumps(user, indent=2, ensure_ascii=False)}")
        else:
            logger.error("Failed to get user info.")

    asyncio.run(main())
