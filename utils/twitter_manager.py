import requests
import json
import logging
from typing import Callable, Optional, Dict, Any

# Try to import botoy, but don't fail if it's not there, to allow standalone execution
try:
    from botoy import jconfig
except ImportError:
    jconfig = None

logger = logging.getLogger(__name__)


class TwitterManager:
    """
    A manager for interacting with Twitter's internal GraphQL API.

    This class provides methods to fetch user information, timelines, and tweet details.
    It also includes parsers to transform the raw API responses into structured data.
    """
    # Feature flags used in Twitter API calls. Stored as constants for clarity.
    _USER_FEATURES = {
        "hidden_profile_subscriptions_enabled": True, "profile_label_improvements_pcf_label_in_post_enabled": True,
        "responsive_web_profile_redirect_enabled": False, "rweb_tipjar_consumption_enabled": True,
        "verified_phone_label_enabled": False, "subscriptions_verification_info_is_identity_verified_enabled": True,
        "subscriptions_verification_info_verified_since_enabled": True, "highlights_tweets_tab_ui_enabled": True,
        "responsive_web_twitter_article_notes_tab_enabled": True, "subscriptions_feature_can_gift_premium": True,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_timeline_navigation_enabled": True
    }
    _TIMELINE_FEATURES = {
        "rweb_video_screen_enabled": False, "profile_label_improvements_pcf_label_in_post_enabled": True,
        "responsive_web_profile_redirect_enabled": False, "rweb_tipjar_consumption_enabled": True,
        "verified_phone_label_enabled": False, "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "premium_content_api_read_enabled": False, "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
        "responsive_web_grok_analyze_post_followups_enabled": True, "responsive_web_jetfuel_frame": True,
        "responsive_web_grok_share_attachment_enabled": True, "articles_preview_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True, "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True, "tweet_awards_web_tipping_enabled": False,
        "responsive_web_grok_show_grok_translated_post": False,
        "responsive_web_grok_analysis_button_from_backend": True,
        "creator_subscriptions_quote_tweet_preview_enabled": False, "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True, "longform_notetweets_inline_media_enabled": True,
        "responsive_web_grok_image_annotation_enabled": True, "responsive_web_grok_imagine_annotation_enabled": True,
        "responsive_web_grok_community_note_auto_translation_is_enabled": False,
        "responsive_web_enhance_cards_enabled": False
    }
    _TWEET_DETAIL_FEATURES = _TIMELINE_FEATURES

    def __init__(self, config: Optional[Dict[str, str]] = None, requests_get_fn: Optional[Callable] = None):
        """
        Initializes the TwitterManager.
        :param config: A dictionary with 'cookie', 'authorization', 'x-csrf-token', and optional 'proxy'.
                       If not provided, it will try to load from botoy's jconfig.
        :param requests_get_fn: A hook function for making GET requests. If not provided, a requests.Session is used.
        """
        if config is None:
            if jconfig:
                self.config = jconfig.get_configuration('twitter')
            else:
                raise ValueError("A config dictionary must be provided when not running in a botoy environment.")
        else:
            self.config = config

        self._requests_get_fn = requests_get_fn
        self.session = None

        if self._requests_get_fn is None:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
                'Referer': 'https://x.com/',
                'x-twitter-auth-type': 'OAuth2Session',
                'cookie': self.config.get('cookie'),
                'authorization': self.config.get('authorization'),
                'x-csrf-token': self.config.get('x-csrf-token')
            })
            if self.config.get('proxy'):
                proxies = {'http': self.config['proxy'], 'https': self.config['proxy']}
                self.session.proxies.update(proxies)

    def _get(self, url: str, params: Dict) -> requests.Response:
        """Internal method to perform GET requests."""
        if self._requests_get_fn:
            # This part maintains backward compatibility with the old hook pattern
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
                'Referer': 'https://x.com/',
                'x-twitter-auth-type': 'OAuth2Session',
                'cookie': self.config.get('cookie'),
                'authorization': self.config.get('authorization'),
                'x-csrf-token': self.config.get('x-csrf-token')
            }
            return self._requests_get_fn(url, headers=headers, params=params)

        return self.session.get(url, params=params)

    # ------------------------ API Methods ------------------------
    def get_user_info(self, user_name: str) -> requests.Response:
        url = 'https://x.com/i/api/graphql/-oaLodhGbbnzJBACb1kk2Q/UserByScreenName'
        params = {
            'variables': json.dumps({"screen_name": user_name, "withGrokTranslatedBio": False}),
            'features': json.dumps(self._USER_FEATURES),
            'fieldToggles': json.dumps({"withPayments": False, "withAuxiliaryUserLabels": True})
        }
        return self._get(url, params)

    def get_user_timeline(self, uid: str) -> requests.Response:
        url = 'https://x.com/i/api/graphql/lZRf8IC-GTuGxDwcsHW8aw/UserTweets'
        params = {
            'variables': json.dumps({
                "userId": uid, "count": 20, "includePromotedContent": True,
                "withQuickPromoteEligibilityTweetFields": True, "withVoice": True
            }),
            'features': json.dumps(self._TIMELINE_FEATURES),
            'fieldToggles': json.dumps({"withArticlePlainText": False})
        }
        return self._get(url, params)

    def get_tweet_detail(self, tid: str) -> requests.Response:
        url = 'https://x.com/i/api/graphql/6QzqakNMdh_YzBAR9SYPkQ/TweetDetail'
        params = {
            'variables': json.dumps({
                "focalTweetId": tid, "referrer": "profile", "with_rux_injections": False, "rankingMode": "Relevance",
                "includePromotedContent": True, "withCommunity": True,
                "withQuickPromoteEligibilityTweetFields": True, "withBirdwatchNotes": True, "withVoice": True
            }),
            'features': json.dumps(self._TWEET_DETAIL_FEATURES),
            'fieldToggles': json.dumps({
                "withArticleRichContentState": True, "withArticlePlainText": False,
                "withGrokAnalyze": False, "withDisallowedReplyControls": False
            })
        }
        return self._get(url, params)

    # ------------------------ Response Parsers ------------------------
    @staticmethod
    def parse_user_info(user_info: Dict) -> Optional[Dict]:
        result = user_info.get('data', {}).get('user', {}).get('result')
        if not result:
            return None
        return TwitterManager.parse_user_result(result)

    @staticmethod
    def parse_user_result(user_result: Dict) -> Dict:
        legacy = user_result.get('legacy', {})
        core = user_result.get('core', {})
        icon_url = user_result.get('avatar', {}).get('image_url') or legacy.get('profile_image_url_https')
        return {
            'id': user_result.get('rest_id'),
            'name': core.get('name') or legacy.get('name'),
            'location': user_result.get('location', {}).get('location', '') or legacy.get('location', ''),
            'description': legacy.get('description'),
            'followers_count': legacy.get('followers_count'),
            'following_count': legacy.get('friends_count'),
            'icon': icon_url
        }

    @staticmethod
    def parse_timeline(timeline: Dict) -> Optional[Dict]:
        if not isinstance(timeline, dict):
            return None
        if 'errors' in timeline:
            return timeline

        # helper: safe get by path list
        def safe_get(obj, path):
            cur = obj
            for p in path:
                if not isinstance(cur, dict) or p not in cur:
                    return None
                cur = cur[p]
            return cur

        # possible locations for instructions (try multiple common shapes)
        candidates = [
            ['data', 'user', 'result', 'timeline_v2', 'timeline', 'instructions'],
            ['data', 'user', 'result', 'timeline', 'timeline', 'instructions'],
            ['data', 'user', 'result', 'timeline', 'instructions'],
            ['data', 'timeline', 'instructions'],
            ['instructions']
        ]

        instructions = None
        for path in candidates:
            val = safe_get(timeline, path)
            if isinstance(val, list):
                instructions = val
                break

        if not instructions:
            logger.warning("Could not find 'instructions' in timeline response.")
            return None

        # find the instruction that contains entries
        entries_source = None
        for instr in instructions:
            if not isinstance(instr, dict):
                continue
            # primary expected type
            if instr.get('type') == 'TimelineAddEntries' and 'entries' in instr:
                entries_source = instr
                break
            # fallback: some responses embed entries under different keys
            if 'entries' in instr:
                entries_source = instr
                break

        if not entries_source:
            logger.warning("Could not find 'entries' in timeline instructions.")
            return None

        entries = entries_source.get('entries') or []
        timeline_data = {}
        for entry in entries:
            try:
                dparsed = TwitterManager.parse_twit_data_one(entry)
                if dparsed and len(dparsed) >= 3 and dparsed[2] is not None:
                    timeline_data[dparsed[0]] = dparsed[2]
            except Exception as e:
                logger.warning(f"Failed to parse a timeline entry: {e}")
                continue
        return timeline_data

    @staticmethod
    def parse_twit_data_one(data: Dict) -> Optional[tuple]:
        tweet_id = data.get('entryId')
        # 跳过广告、who_to_follow等非tweet条目
        if not tweet_id or not tweet_id.startswith('tweet-'):
            return None
        
        content = data.get('content', {})
        entry_type = content.get('entryType')

        result = None
        if entry_type == 'TimelineTimelineItem':
            item_content = content.get('itemContent', {})
            if item_content.get('tweetDisplayType') in ['SelfThread', 'Tweet']:
                result = TwitterManager.get_tweet_result(item_content.get('tweet_results', {}).get('result'))
        elif entry_type == 'TimelineTimelineModule' and content.get('tweetDisplayType') == 'VerticalConversation':
            result = TwitterManager.get_tweet_result(content.get('items', [{}])[-1].get('item', {}).get('tweet_results', {}).get('result'))

        if not result:
            return None

        if result.get('__typename') == 'TweetWithVisibilityResults':
            result = result.get('tweet', {})

        legacy = result.get('legacy')
        user_result = result.get('core', {}).get('user_results', {}).get('result')

        if not legacy or not user_result:
            return None
            
        tweet_data = TwitterManager.parse_legacy(legacy)
        user_info = TwitterManager.parse_user_result(user_result)
        return tweet_id, entry_type, tweet_data, user_info

    @staticmethod
    def get_tweet_result(result: Dict) -> Dict:
        return result.get('tweet') if result and result.get('__typename') == 'TweetWithVisibilityResults' else result

    @staticmethod
    def parse_legacy(legacy: Dict) -> Dict:
        tweet_data = {'tweet_type': 'default'}
        
        if 'quoted_status_result' in legacy:
            tweet_data['tweet_type'] = 'quote'
            sub_result = TwitterManager.get_tweet_result(legacy['quoted_status_result'].get('result', {}))
            if sub_result:
                tweet_data['quote_data'] = {
                    'user_info': TwitterManager.parse_user_result(sub_result.get('core', {}).get('user_results', {}).get('result', {})),
                    'data': TwitterManager.parse_legacy(sub_result.get('legacy', {}))
                }
        elif 'retweeted_status_result' in legacy:
            tweet_data['tweet_type'] = 'retweet'
            sub_result = TwitterManager.get_tweet_result(legacy['retweeted_status_result'].get('result', {}))
            if sub_result:
                tweet_data['retweet_data'] = {
                    'user_info': TwitterManager.parse_user_result(sub_result.get('core', {}).get('user_results', {}).get('result', {})),
                    'data': TwitterManager.parse_legacy(sub_result.get('legacy', {}))
                }

        tweet_data['text'] = legacy.get('full_text')
        tweet_data['id'] = legacy.get('conversation_id_str')
        tweet_data['created_at'] = legacy.get('created_at')
        
        media = legacy.get('extended_entities', {}).get('media', [])
        tweet_data['imgs'] = [m['media_url_https'] for m in media if m.get('type') == 'photo']
        tweet_data['videos'] = [
            r['url'] for m in media if m.get('type') == 'video' and m.get('video_info', {}).get('variants')
            for r in m['video_info']['variants'] if r.get('content_type') == 'video/mp4'
        ]
        return tweet_data

    @staticmethod
    def parse_tweet_detail(tweet_detail: Dict) -> tuple:
        instructions = tweet_detail.get('data', {}).get('threaded_conversation_with_injections_v2', {}).get('instructions', [])
        entry = next((e for i in instructions if i.get('type') == 'TimelineAddEntries' for e in reversed(i.get('entries', []))), None)
        
        if entry:
            dparsed = TwitterManager.parse_twit_data_one(entry)
            if dparsed and dparsed[2] is not None:
                return dparsed[2], dparsed[3]
        return None, None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # To run this script locally, fill in your Twitter credentials and proxy settings below.
    local_config = {
      "cookie": "your_cookie_here",
      "authorization": "your_authorization_here",
      "x-csrf-token": "your_csrf_token_here",
      "proxy": "http://127.0.0.1:7890" # e.g., http://127.0.0.1:7890 or socks5://127.0.0.1:7891
    }

    # Basic check if the config is filled
    if 'your_cookie_here' in local_config.get('cookie', ''):
        logger.error("Please fill in your Twitter credentials in the `local_config` dictionary.")
    else:
        tm = TwitterManager(config=local_config)
        
        # --- Test get_user_info ---
        logger.info("--- Testing get_user_info ---")
        user_name_to_test = 'gume0612'
        try:
            res = tm.get_user_info(user_name_to_test)
            if res.status_code == 200:
                user_data = res.json()
                logger.info(f"Raw user info for {user_name_to_test}: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
                parsed_user = tm.parse_user_info(user_data)
                logger.info(f"Parsed user info: {parsed_user}")
                
                # --- Test get_user_timeline ---
                if parsed_user and parsed_user.get('id'):
                    logger.info("\n--- Testing get_user_timeline ---")
                    uid = parsed_user['id']
                    res_tl = tm.get_user_timeline(uid)
                    if res_tl.status_code == 200:
                        tl_data = res_tl.json()
                        logger.info(f"Raw timeline for {uid}: {json.dumps(tl_data, indent=2, ensure_ascii=False)}")
                        parsed_tl = tm.parse_timeline(tl_data)
                        if parsed_tl:
                            logger.info(f"Parsed timeline has {len(parsed_tl)} tweets.")
                        else:
                            logger.warning("Could not parse timeline.")
                    else:
                        logger.error(f"Failed to get timeline. Status: {res_tl.status_code}, Body: {res_tl.text}")
            else:
                logger.error(f"Failed to get user info. Status: {res.status_code}, Body: {res.text}")
        except Exception as e:
            logger.exception(f"An error occurred during testing: {e}")