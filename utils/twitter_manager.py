import requests
import json
import logging

from botoy import jconfig

logger = logging.getLogger(__name__)

class TwitterManager():
    def __init__(self, requests_get_fn=None) -> None:
        '''
        :param requests_hook: request请求时调用函数的钩子。不传入时使用requests标准库请求
        '''
        self.__requests_get = requests.get
        
        # get config
        twitter_conf = jconfig.get_configuration('twitter')
        self.__headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
            'Referer': 'https://x.com/',
            'x-twitter-auth-type': 'OAuth2Session',
            'cookie': twitter_conf.get('cookie'),
            'authorization': twitter_conf.get('authorization'),
            'x-csrf-token': twitter_conf.get('x-csrf-token')
        }
        
        if requests_get_fn is not None:
            self.register_requests_hook(requests_get_fn)
            
    def register_requests_hook(self, requests_get_fn):
        '''
        注册request请求时调用函数的钩子
        '''
        self.__requests_get = requests_get_fn
        
    def get_user_info(self, user_name):
        url = 'https://x.com/i/api/graphql/-oaLodhGbbnzJBACb1kk2Q/UserByScreenName'
        params = {
            'variables': json.dumps({
                "screen_name": user_name,
                "withGrokTranslatedBio": False
            }),
            'features': json.dumps({
                "hidden_profile_subscriptions_enabled":True,
                "profile_label_improvements_pcf_label_in_post_enabled":True,
                "responsive_web_profile_redirect_enabled":False,
                "rweb_tipjar_consumption_enabled":True,
                "verified_phone_label_enabled":False,
                "subscriptions_verification_info_is_identity_verified_enabled":True,
                "subscriptions_verification_info_verified_since_enabled":True,
                "highlights_tweets_tab_ui_enabled":True,
                "responsive_web_twitter_article_notes_tab_enabled":True,
                "subscriptions_feature_can_gift_premium":True,
                "creator_subscriptions_tweet_preview_api_enabled":True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled":False,
                "responsive_web_graphql_timeline_navigation_enabled":True
            }),
            'fieldToggles': json.dumps({
                "withPayments":False,
                "withAuxiliaryUserLabels":True
            })
        }
        return self.__get(url, params)
    
    def get_user_timeline(self, uid):
        url = 'https://x.com/i/api/graphql/lZRf8IC-GTuGxDwcsHW8aw/UserTweets'
        params = {
            'variables': json.dumps({
                "userId":uid,
                "count":20,
                "includePromotedContent":True,
                "withQuickPromoteEligibilityTweetFields":True,
                "withVoice":True
            }),
            'features': json.dumps({
                "rweb_video_screen_enabled":False,
                "profile_label_improvements_pcf_label_in_post_enabled":True,
                "responsive_web_profile_redirect_enabled":False,
                "rweb_tipjar_consumption_enabled":True,
                "verified_phone_label_enabled":False,
                "creator_subscriptions_tweet_preview_api_enabled":True,
                "responsive_web_graphql_timeline_navigation_enabled":True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled":False,
                "premium_content_api_read_enabled":False,
                "communities_web_enable_tweet_community_results_fetch":True,
                "c9s_tweet_anatomy_moderator_badge_enabled":True,
                "responsive_web_grok_analyze_button_fetch_trends_enabled":False,
                "responsive_web_grok_analyze_post_followups_enabled":True,
                "responsive_web_jetfuel_frame":True,
                "responsive_web_grok_share_attachment_enabled":True,
                "articles_preview_enabled":True,
                "responsive_web_edit_tweet_api_enabled":True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled":True,
                "view_counts_everywhere_api_enabled":True,
                "longform_notetweets_consumption_enabled":True,
                "responsive_web_twitter_article_tweet_consumption_enabled":True,
                "tweet_awards_web_tipping_enabled":False,
                "responsive_web_grok_show_grok_translated_post":False,
                "responsive_web_grok_analysis_button_from_backend":True,
                "creator_subscriptions_quote_tweet_preview_enabled":False,
                "freedom_of_speech_not_reach_fetch_enabled":True,
                "standardized_nudges_misinfo":True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":True,
                "longform_notetweets_rich_text_read_enabled":True,
                "longform_notetweets_inline_media_enabled":True,
                "responsive_web_grok_image_annotation_enabled":True,
                "responsive_web_grok_imagine_annotation_enabled":True,
                "responsive_web_grok_community_note_auto_translation_is_enabled":False,
                "responsive_web_enhance_cards_enabled":False
            }),
            'fieldToggles': json.dumps({"withArticlePlainText":False})
        }
        return self.__get(url, params)
    
    def get_tweet_detail(self, tid):
        url = 'https://x.com/i/api/graphql/6QzqakNMdh_YzBAR9SYPkQ/TweetDetail'
        params = {
            'variables': json.dumps({
                "focalTweetId":tid,
                "referrer":"profile",
                "with_rux_injections":False,
                "rankingMode":"Relevance",
                "includePromotedContent":True,
                "withCommunity":True,
                "withQuickPromoteEligibilityTweetFields":True,
                "withBirdwatchNotes":True,
                "withVoice":True
            }),
            'features': json.dumps({
                "rweb_video_screen_enabled":False,
                "profile_label_improvements_pcf_label_in_post_enabled":True,
                "responsive_web_profile_redirect_enabled":False,
                "rweb_tipjar_consumption_enabled":True,
                "verified_phone_label_enabled":False,
                "creator_subscriptions_tweet_preview_api_enabled":True,
                "responsive_web_graphql_timeline_navigation_enabled":True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled":False,
                "premium_content_api_read_enabled":False,
                "communities_web_enable_tweet_community_results_fetch":True,
                "c9s_tweet_anatomy_moderator_badge_enabled":True,
                "responsive_web_grok_analyze_button_fetch_trends_enabled":False,
                "responsive_web_grok_analyze_post_followups_enabled":True,
                "responsive_web_jetfuel_frame":True,
                "responsive_web_grok_share_attachment_enabled":True,
                "articles_preview_enabled":True,
                "responsive_web_edit_tweet_api_enabled":True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled":True,
                "view_counts_everywhere_api_enabled":True,
                "longform_notetweets_consumption_enabled":True,
                "responsive_web_twitter_article_tweet_consumption_enabled":True,
                "tweet_awards_web_tipping_enabled":False,
                "responsive_web_grok_show_grok_translated_post":False,
                "responsive_web_grok_analysis_button_from_backend":True,
                "creator_subscriptions_quote_tweet_preview_enabled":False,
                "freedom_of_speech_not_reach_fetch_enabled":True,
                "standardized_nudges_misinfo":True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":True,
                "longform_notetweets_rich_text_read_enabled":True,
                "longform_notetweets_inline_media_enabled":True,
                "responsive_web_grok_image_annotation_enabled":True,
                "responsive_web_grok_imagine_annotation_enabled":True,
                "responsive_web_grok_community_note_auto_translation_is_enabled":False,
                "responsive_web_enhance_cards_enabled":False
            }),
            'fieldToggles': json.dumps({
                "withArticleRichContentState":True,
                "withArticlePlainText":False,
                "withGrokAnalyze":False,
                "withDisallowedReplyControls":False
            })
        }
        return self.__get(url, params)
    
    def __get(self, url, params):
        return self.__requests_get(url, headers=self.__headers, params=params)
    
    # ------------------------ 解析返回json ------------------------
    @staticmethod
    def parse_user_info(user_info):
        # 用户不存在
        if not user_info.get('data'):
            return None
        result = user_info['data']['user']['result']
        user_info = TwitterManager.parse_user_result(result)
        return user_info
    
    @staticmethod
    def parse_user_result(user_result):
        legacy = user_result.get('legacy', {})
        core = user_result.get('core', {})

        # The icon URL can be in the top-level avatar object or fallback to the legacy object
        icon_url = user_result.get('avatar', {}).get('image_url')
        if not icon_url:
            icon_url = legacy.get('profile_image_url_https')

        user_info = dict(
            id=user_result.get('rest_id'),
            name=core.get('name') or legacy.get('name'),
            location=user_result.get('location', {}).get('location') or legacy.get('location'),
            description=legacy.get('description'),
            followers_count=legacy.get('followers_count'),
            following_count=legacy.get('friends_count'),
            icon=icon_url
        )
        return user_info
    
    @staticmethod
    def parse_timeline(timeline):
        logger.info(f'>>>>>>>>>>>>> twitter timeline: {timeline}')
        if 'data' not in timeline:
            # handle error
            if 'errors' in timeline:
                return timeline
            return None
        # uid不存在
        if not timeline['data'].get('user'):
            return None
        instructions = timeline['data']['user']['result']['timeline_v2']['timeline']['instructions']
        timeline_data_source = None
        for i in instructions:
            if i['type'] == 'TimelineAddEntries':
                timeline_data_source = i
                break
        # 时间线不存在
        if timeline_data_source is None:
            return None
        timeline_data = dict()
        for dsource in timeline_data_source['entries']:
            dparsed = TwitterManager.parse_twit_data_one(dsource)
            if dparsed[2] is None:
                continue
            timeline_data[dparsed[0]] = dparsed[2]
        return timeline_data
        
    @staticmethod
    def parse_twit_data_one(data):
        '''
        :return: tweet_id, entry_type, parsed_data_list
        '''
        tweet_id = data['entryId']
        content = data['content']
        entry_type = content['entryType']
        
        if entry_type == 'TimelineTimelineItem':
             if 'tweetDisplayType' not in content['itemContent'] or content['itemContent']['tweetDisplayType'] not in ['SelfThread', 'Tweet']:
                 return tweet_id, entry_type, None, None
             result = TwitterManager.get_tweet_result(content['itemContent']['tweet_results']['result'])
        elif entry_type == 'TimelineTimelineModule':
            if 'tweetDisplayType' not in content:
                return tweet_id, entry_type, None, None
            if content['tweetDisplayType'] == 'VerticalConversation':
                result = TwitterManager.get_tweet_result(content['items'][-1]['item']['tweet_results']['result'])
            else:
                return tweet_id, entry_type, None, None
        else:
            return tweet_id, entry_type, None, None
        
        if result.get('__typename', '') == 'TweetWithVisibilityResults':
            result = result['tweet']
        
        legacy = result['legacy']
        tweet_data = TwitterManager.parse_legacy(legacy)
        user_result = result['core']['user_results']['result']
        user_info=TwitterManager.parse_user_result(user_result)
        return tweet_id, entry_type, tweet_data, user_info
    
    @staticmethod
    def get_tweet_result(result):
        '''
        判断推类型，不同类型可能会使后续数据结构不完全一致
        '''
        result_type = result['__typename']
        if result_type == 'TweetWithVisibilityResults':
            return result['tweet']
        return result
            
    @staticmethod
    def parse_legacy(legacy):
        tweet_data = dict()
        if 'quoted_status_result' in legacy:
            tweet_data['tweet_type'] = 'quote'
            sub_result = TwitterManager.get_tweet_result(legacy['quoted_status_result']['result'])
            tweet_data['quote_data'] = dict(
                user_info=TwitterManager.parse_user_result(sub_result['core']['user_results']['result']),
                data=TwitterManager.parse_legacy(sub_result['legacy'])
            )
        elif 'retweeted_status_result' in legacy:
            tweet_data['tweet_type'] = 'retweet'
            sub_result = TwitterManager.get_tweet_result(legacy['retweeted_status_result']['result'])
            tweet_data['retweet_data'] = dict(
                user_info=TwitterManager.parse_user_result(sub_result['core']['user_results']['result']),
                data=TwitterManager.parse_legacy(sub_result['legacy'])
            )
        else:
            tweet_data['tweet_type'] = 'default'
            
        tweet_data['text'] = legacy['full_text']
        tweet_data['id'] = legacy['conversation_id_str']
        tweet_data['created_at'] = legacy['created_at']
        if 'extended_entities' in legacy and 'media' in legacy['extended_entities']:
            tweet_data['imgs'] = [m['media_url_https'] for m in legacy['extended_entities']['media'] if m['type'] == 'photo']
            tweet_data['videos'] = [
                r['url']
                for m in legacy['extended_entities']['media'] 
                if m['type'] == 'video' and m.get('video_info', {}).get('variants', [])
                for r in m['video_info']['variants']
                if r['content_type'] == 'video/mp4'
            ]
        
        return tweet_data
    
    @staticmethod
    def parse_tweet_detail(tweet_detail):
        frame = tweet_detail['data'].get('threaded_conversation_with_injections_v2')
        if not frame:
            return None, None
        instructions = frame['instructions']
        TimelineAddEntries = None
        for i in instructions:
            if i['type'] == 'TimelineAddEntries':
                TimelineAddEntries = i
                break
        if not TimelineAddEntries:
            return None, None
        entries = TimelineAddEntries['entries']
        for e in entries[::-1]:
            dparsed = TwitterManager.parse_twit_data_one(e)
            if dparsed[2] is not None:
                return dparsed[2], dparsed[3]
        return None, None
    # ------------------------ 解析返回json ------------------------
    
# for test
if __name__ == '__main__':
    tm = TwitterManager()
    res = tm.get_user_info('gume0612')
    # print(res.status_code, res.json())
    res = res.json()
    # print(tm.parse_user_info(res))
    uid = res['data']['user']['result']['rest_id']
    res = tm.get_user_timeline(uid)
    logger.info(res.text)
    try:
        logger.info("status: %s json: %s", res.status_code, res.json())
    except Exception:
        logger.info("status: %s (failed to decode json)", res.status_code)
    # print(tm.parse_timeline(res.json()))
    
    # res = tm.get_tweet_detail('1675777787368722433')
    # print(res.status_code, res.json())
    # tdata, user_info = tm.parse_tweet_detail(res.json())
    # tweet_type = tdata['tweet_type']
    # if tweet_type == 'default':
    #     imgs = tdata.get('imgs')
    # elif tweet_type == 'retweet':
    #     retweet_data = tdata['retweet_data']
    #     imgs = retweet_data['data'].get('imgs')
    # elif tweet_type == 'quote':
    #     quote_data = tdata['quote_data']
    #     imgs = quote_data['data'].get('imgs')
    # print(tdata)
    # if imgs:
    #     print(imgs)
