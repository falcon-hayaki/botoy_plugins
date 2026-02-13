import requests
import logging
from typing import Optional, Dict, Any, List

# Try to import botoy, but don't fail if it's not there, to allow standalone execution
try:
    from botoy import jconfig
except ImportError:
    jconfig = None

logger = logging.getLogger(__name__)


class XAPIManager:
    """
    A manager for interacting with X (Twitter) Official API v2.
    
    This class provides methods to fetch user information and tweets using the official API.
    It requires an API Bearer Token for authentication.
    """
    
    # X API v2 base URL
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initializes the XAPIManager.
        
        :param config: A dictionary with 'bearer_token' and optional 'proxy', 'api_tier'.
                       If not provided, it will try to load from botoy's jconfig.
                       api_tier options: 'free', 'basic', 'pro' (default: 'free')
        """
        if config is None:
            if jconfig:
                self.config = jconfig.get_configuration('x_api')
            else:
                raise ValueError("A config dictionary must be provided when not running in a botoy environment.")
        else:
            self.config = config
        
        # Set API tier (free, basic, pro)
        self.api_tier = self.config.get('api_tier', 'free').lower()
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.get("bearer_token")}',
            'User-Agent': 'v2UserLookupPython'
        })
        
        if self.config.get('proxy'):
            proxies = {'http': self.config['proxy'], 'https': self.config['proxy']}
            self.session.proxies.update(proxies)
    
    def _get_user_fields(self) -> str:
        """
        Get user fields based on API tier.
        Free tier has limitations on certain fields.
        """
        base_fields = 'id,name,username,description,profile_image_url,public_metrics,created_at'
        
        if self.api_tier in ['basic', 'pro', 'enterprise']:
            # Paid tiers can access additional fields
            return base_fields + ',verified,url,location'
        else:
            # Free tier - basic fields only
            return base_fields
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Internal method to perform GET requests."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    # ------------------------ API Methods ------------------------
    
    def get_user_by_username(self, username: str) -> requests.Response:
        """
        Get user information by username.
        
        :param username: The Twitter username (without @)
        :return: Response object
        """
        endpoint = f"users/by/username/{username}"
        params = {
            'user.fields': self._get_user_fields()
        }
        return self._get(endpoint, params)
    
    def get_user_by_id(self, user_id: str) -> requests.Response:
        """
        Get user information by user ID.
        
        :param user_id: The Twitter user ID
        :return: Response object
        """
        endpoint = f"users/{user_id}"
        params = {
            'user.fields': self._get_user_fields()
        }
        return self._get(endpoint, params)
    
    def get_user_tweets(
        self, 
        user_id: str, 
        max_results: int = 10,
        since_id: Optional[str] = None,
        until_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        exclude: Optional[str] = None,
        pagination_token: Optional[str] = None
    ) -> requests.Response:
        """
        Get tweets from a specific user.
        
        :param user_id: The Twitter user ID
        :param max_results: Maximum number of tweets to return (default: 10, max: 100)
        :param since_id: Returns results with a Tweet ID greater than (newer than) the specified ID
        :param until_id: Returns results with a Tweet ID less than (older than) the specified ID
        :param start_time: YYYY-MM-DDTHH:mm:ssZ format. The earliest UTC timestamp
        :param end_time: YYYY-MM-DDTHH:mm:ssZ format. The latest UTC timestamp
        :param exclude: Comma-separated list of types to exclude (e.g., 'retweets,replies')
        :param pagination_token: Token to get the next page of results
        :return: Response object
        """
        endpoint = f"users/{user_id}/tweets"
        
        # Base tweet fields (available in all tiers)
        tweet_fields = 'id,text,created_at,author_id,public_metrics,attachments,entities'
        if self.api_tier in ['basic', 'pro', 'enterprise']:
            tweet_fields += ',referenced_tweets'
        
        params = {
            'max_results': min(max_results, 100),
            'tweet.fields': tweet_fields,
            'media.fields': 'url,preview_image_url,type,media_key',
            'user.fields': 'id,name,username,profile_image_url',
            'expansions': 'attachments.media_keys,author_id'
        }
        
        # Add additional expansions for paid tiers
        if self.api_tier in ['basic', 'pro', 'enterprise']:
            params['media.fields'] += ',duration_ms,height,width'
            params['expansions'] += ',referenced_tweets.id'
        
        # Add optional parameters if provided
        if since_id:
            params['since_id'] = since_id
        if until_id:
            params['until_id'] = until_id
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if exclude:
            params['exclude'] = exclude
        if pagination_token:
            params['pagination_token'] = pagination_token
        
        return self._get(endpoint, params)
    
    def get_tweet(self, tweet_id: str) -> requests.Response:
        """
        Get a specific tweet by ID.
        
        :param tweet_id: The Tweet ID
        :return: Response object
        """
        endpoint = f"tweets/{tweet_id}"
        
        # Base fields for free tier
        tweet_fields = 'id,text,created_at,author_id,public_metrics,attachments,entities'
        media_fields = 'url,preview_image_url,type,media_key'
        user_fields = 'id,name,username,profile_image_url'
        expansions = 'attachments.media_keys,author_id'
        
        # Enhanced fields for paid tiers
        if self.api_tier in ['basic', 'pro', 'enterprise']:
            tweet_fields += ',referenced_tweets,lang'
            media_fields += ',duration_ms,height,width'
            expansions += ',referenced_tweets.id'
        
        params = {
            'tweet.fields': tweet_fields,
            'media.fields': media_fields,
            'user.fields': user_fields,
            'expansions': expansions
        }
        
        # Only add poll and place fields for paid tiers
        if self.api_tier in ['pro', 'enterprise']:
            params['poll.fields'] = 'id,options,duration_minutes,end_datetime,voting_status'
            params['place.fields'] = 'id,full_name,country,country_code,geo,name,place_type'
            params['expansions'] += ',attachments.poll_ids,geo.place_id'
        
        return self._get(endpoint, params)
    
    def get_tweets(self, tweet_ids: List[str]) -> requests.Response:
        """
        Get multiple tweets by IDs (up to 100).
        
        :param tweet_ids: List of Tweet IDs (max 100)
        :return: Response object
        """
        if len(tweet_ids) > 100:
            logger.warning(f"Too many tweet IDs provided ({len(tweet_ids)}). Only first 100 will be used.")
            tweet_ids = tweet_ids[:100]
        
        endpoint = "tweets"
        
        # Base fields for free tier
        tweet_fields = 'id,text,created_at,author_id,public_metrics,attachments,entities'
        media_fields = 'url,preview_image_url,type,media_key'
        user_fields = 'id,name,username,profile_image_url'
        expansions = 'attachments.media_keys,author_id'
        
        # Enhanced fields for paid tiers
        if self.api_tier in ['basic', 'pro', 'enterprise']:
            tweet_fields += ',referenced_tweets,lang'
            media_fields += ',duration_ms,height,width'
            expansions += ',referenced_tweets.id'
        
        params = {
            'ids': ','.join(tweet_ids),
            'tweet.fields': tweet_fields,
            'media.fields': media_fields,
            'user.fields': user_fields,
            'expansions': expansions
        }
        
        # Only add poll and place fields for paid tiers
        if self.api_tier in ['pro', 'enterprise']:
            params['poll.fields'] = 'id,options,duration_minutes,end_datetime,voting_status'
            params['place.fields'] = 'id,full_name,country,country_code,geo,name,place_type'
            params['expansions'] += ',attachments.poll_ids,geo.place_id'
        
        return self._get(endpoint, params)
    
    def get_user_mentions(
        self,
        user_id: str,
        max_results: int = 10,
        since_id: Optional[str] = None,
        until_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        pagination_token: Optional[str] = None
    ) -> requests.Response:
        """
        Get tweets that mention a specific user.
        
        :param user_id: The Twitter user ID
        :param max_results: Maximum number of tweets to return (default: 10, max: 100)
        :param since_id: Returns results with a Tweet ID greater than the specified ID
        :param until_id: Returns results with a Tweet ID less than the specified ID
        :param start_time: YYYY-MM-DDTHH:mm:ssZ format. The earliest UTC timestamp
        :param end_time: YYYY-MM-DDTHH:mm:ssZ format. The latest UTC timestamp
        :param pagination_token: Token to get the next page of results
        :return: Response object
        """
        endpoint = f"users/{user_id}/mentions"
        
        # Base fields for free tier
        tweet_fields = 'id,text,created_at,author_id,public_metrics,attachments,entities'
        
        # Enhanced fields for paid tiers
        if self.api_tier in ['basic', 'pro', 'enterprise']:
            tweet_fields += ',referenced_tweets'
        
        params = {
            'max_results': min(max_results, 100),
            'tweet.fields': tweet_fields,
            'media.fields': 'url,preview_image_url,type,media_key',
            'user.fields': 'id,name,username,profile_image_url',
            'expansions': 'attachments.media_keys,author_id'
        }
        
        # Add additional fields for paid tiers
        if self.api_tier in ['basic', 'pro', 'enterprise']:
            params['media.fields'] += ',duration_ms,height,width'
            params['expansions'] += ',referenced_tweets.id'
        
        # Add optional parameters if provided
        if since_id:
            params['since_id'] = since_id
        if until_id:
            params['until_id'] = until_id
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if pagination_token:
            params['pagination_token'] = pagination_token
            
        return self._get(endpoint, params)
    
    def get_usage(self) -> requests.Response:
        """
        Get API usage.
        Reference: https://developer.x.com/en/docs/twitter-api/usage/tweets/api-reference/get-usage-tweets
        """
        endpoint = "usage/tweets"
        return self._get(endpoint)
    
    # ------------------------ Response Parsers ------------------------
    
    @staticmethod
    def parse_user(response_data: Dict) -> Optional[Dict]:
        """
        Parse user data from API response.
        
        :param response_data: API response JSON
        :return: Parsed user data or None
        """
        if 'data' not in response_data:
            logger.error(f"No data in response: {response_data}")
            return None
        
        user = response_data['data']
        public_metrics = user.get('public_metrics', {})
        
        return {
            'id': user.get('id'),
            'name': user.get('name'),
            'username': user.get('username'),
            'description': user.get('description'),
            'location': user.get('location', ''),
            'icon': user.get('profile_image_url', '').replace('_normal', '_400x400'),  # Get higher quality image
            'followers_count': public_metrics.get('followers_count', 0),
            'following_count': public_metrics.get('following_count', 0),
            'tweet_count': public_metrics.get('tweet_count', 0),
            'created_at': user.get('created_at')
        }
    
    @staticmethod
    def parse_tweets(response_data: Dict) -> Optional[Dict]:
        """
        Parse tweets data from API response.
        
        :param response_data: API response JSON
        :return: Dictionary containing parsed tweets and metadata, or None
        """
        if 'data' not in response_data:
            logger.error(f"No data in response: {response_data}")
            return None
        
        tweets = response_data['data']
        includes = response_data.get('includes', {})
        media_map = {m['media_key']: m for m in includes.get('media', [])}
        users_map = {u['id']: u for u in includes.get('users', [])}
        
        parsed_tweets = []
        for tweet in tweets:
            parsed_tweet = XAPIManager.parse_tweet(tweet, media_map, users_map)
            if parsed_tweet:
                parsed_tweets.append(parsed_tweet)
        
        # Include pagination metadata
        result = {
            'tweets': parsed_tweets,
            'meta': response_data.get('meta', {})
        }
        
        return result
    
    @staticmethod
    def parse_tweet(tweet: Dict, media_map: Optional[Dict] = None, users_map: Optional[Dict] = None) -> Dict:
        """
        Parse a single tweet.
        
        :param tweet: Tweet data
        :param media_map: Optional media map from includes
        :param users_map: Optional users map from includes
        :return: Parsed tweet data
        """
        if media_map is None:
            media_map = {}
        if users_map is None:
            users_map = {}
        
        tweet_data = {
            'id': tweet.get('id'),
            'text': tweet.get('text'),
            'created_at': tweet.get('created_at'),
            'author_id': tweet.get('author_id'),
            'lang': tweet.get('lang'),
            'imgs': [],
            'videos': []
        }
        
        # Add author info if available
        author_id = tweet.get('author_id')
        if author_id and author_id in users_map:
            author = users_map[author_id]
            tweet_data['author'] = {
                'id': author.get('id'),
                'name': author.get('name'),
                'username': author.get('username'),
                'profile_image_url': author.get('profile_image_url'),
                'verified': author.get('verified', False)
            }
        
        # Parse metrics
        public_metrics = tweet.get('public_metrics', {})
        tweet_data['metrics'] = {
            'retweet_count': public_metrics.get('retweet_count', 0),
            'reply_count': public_metrics.get('reply_count', 0),
            'like_count': public_metrics.get('like_count', 0),
            'quote_count': public_metrics.get('quote_count', 0),
            'impression_count': public_metrics.get('impression_count', 0)
        }
        
        # Parse referenced tweets (retweets, replies, quotes)
        referenced_tweets = tweet.get('referenced_tweets', [])
        if referenced_tweets:
            tweet_data['referenced_tweets'] = [
                {'type': ref.get('type'), 'id': ref.get('id')}
                for ref in referenced_tweets
            ]
        
        # Parse media attachments
        attachments = tweet.get('attachments', {})
        media_keys = attachments.get('media_keys', [])
        
        for media_key in media_keys:
            media = media_map.get(media_key, {})
            media_type = media.get('type')
            
            if media_type == 'photo':
                tweet_data['imgs'].append(media.get('url'))
            elif media_type == 'video' or media_type == 'animated_gif':
                video_info = {
                    'preview': media.get('preview_image_url'),
                    'type': media_type,
                    'duration_ms': media.get('duration_ms'),
                    'height': media.get('height'),
                    'width': media.get('width')
                }
                tweet_data['videos'].append(video_info)
        
        # Parse entities (urls, hashtags, mentions)
        entities = tweet.get('entities', {})
        if entities:
            tweet_data['entities'] = {
                'urls': entities.get('urls', []),
                'hashtags': entities.get('hashtags', []),
                'mentions': entities.get('mentions', [])
            }
        
        return tweet_data


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # To run this script locally, fill in your X API credentials
    local_config = {
        "bearer_token": "AAAAAAAAAAAAAAAAAAAAAIdT7gEAAAAAPXimHNRv8WGiDiZO7upbnWXGjPI%3DniVfuzaFx1fGaozd7yVkUiCgXyHHJDREBMHKoi4RNnInptFgDM",
        "proxy": "http://127.0.0.1:7897"  # Optional: e.g., http://127.0.0.1:7890
    }
    
    # Basic check if the config is filled
    if 'your_bearer_token_here' in local_config.get('bearer_token', ''):
        logger.error("Please fill in your X API bearer token in the `local_config` dictionary.")
        logger.info("You can get a bearer token from: https://developer.twitter.com/")
    else:
        xm = XAPIManager(config=local_config)
        
        # --- Test get_user_by_username ---
        logger.info("--- Testing get_user_by_username ---")
        username_to_test = 'elonmusk'  # 使用更可靠的测试账号
        try:
            res = xm.get_user_by_username(username_to_test)
            if res.status_code == 200:
                user_data = res.json()
                logger.info(f"Raw user info: {user_data}")
                parsed_user = xm.parse_user(user_data)
                
                if not parsed_user:
                    logger.error("Failed to parse user data")
                else:
                    logger.info(f"Parsed user info: {parsed_user}")
                    
                    # --- Test get_user_tweets with advanced parameters ---
                    if parsed_user.get('id'):
                        logger.info("\n--- Testing get_user_tweets with parameters ---")
                        user_id = parsed_user['id']
                        
                        # Example 1: Basic query
                        res_tweets = xm.get_user_tweets(user_id, max_results=5)
                        if res_tweets.status_code == 200:
                            tweets_data = res_tweets.json()
                            logger.info(f"Raw tweets response received")
                            
                            parsed_result = xm.parse_tweets(tweets_data)
                            if not parsed_result:
                                logger.warning("No tweets data returned (might be an error response)")
                                logger.info(f"Response: {tweets_data}")
                            else:
                                logger.info(f"Parsed {len(parsed_result['tweets'])} tweets")
                                logger.info(f"Metadata: {parsed_result['meta']}")
                                
                                for idx, tweet in enumerate(parsed_result['tweets'][:3], 1):  # 只显示前3条
                                    logger.info(f"\nTweet {idx}: {tweet.get('text')[:80]}...")
                                    if tweet.get('author'):
                                        logger.info(f"  Author: @{tweet['author']['username']}")
                                    if tweet.get('referenced_tweets'):
                                        logger.info(f"  References: {tweet['referenced_tweets']}")
                                    logger.info(f"  Metrics: ❤️{tweet['metrics']['like_count']} | 🔁{tweet['metrics']['retweet_count']}")
                                
                                # Example 2: Query with exclude parameter
                                logger.info("\n--- Testing get_user_tweets (exclude retweets) ---")
                                res_no_rt = xm.get_user_tweets(user_id, max_results=5, exclude='retweets')
                                if res_no_rt.status_code == 200:
                                    no_rt_data = xm.parse_tweets(res_no_rt.json())
                                    if no_rt_data:
                                        logger.info(f"Got {len(no_rt_data['tweets'])} tweets without retweets")
                                    else:
                                        logger.warning("No tweets data (might be filtered out)")
                                
                                # --- Test get_tweets (batch query) ---
                                logger.info("\n--- Testing get_tweets (batch query) ---")
                                if len(parsed_result['tweets']) > 0:
                                    tweet_ids = [t['id'] for t in parsed_result['tweets'][:3]]
                                    logger.info(f"Querying {len(tweet_ids)} tweets in batch...")
                                    res_batch = xm.get_tweets(tweet_ids)
                                    if res_batch.status_code == 200:
                                        batch_result = xm.parse_tweets(res_batch.json())
                                        if batch_result:
                                            logger.info(f"✅ Batch query returned {len(batch_result['tweets'])} tweets")
                        else:
                            logger.error(f"Failed to get tweets. Status: {res_tweets.status_code}, Body: {res_tweets.text}")
                    
                    logger.info("\n" + "="*60)
                    logger.info("✅ 测试完成！API 访问正常")
                    logger.info("="*60)
            else:
                logger.error(f"Failed to get user info. Status: {res.status_code}, Body: {res.text}")
        except Exception as e:
            logger.exception(f"An error occurred during testing: {e}")
