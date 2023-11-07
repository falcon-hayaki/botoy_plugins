import requests
import json

from botoy import jconfig

class TwitterManager():
    def __init__(self, requests_get_fn=None) -> None:
        '''
        :param requests_hook: request请求时调用函数的钩子。不传入时使用requests标准库请求
        '''
        self.__requests_get = requests.get
        
        # get config
        twitter_conf = jconfig.get_configuration('twitter')
        self.__headers = {
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
        url = 'https://twitter.com/i/api/graphql/vG3rchZtwqiwlKgUYCrTRA/UserByScreenName'
        params = {
            'variables': json.dumps({"screen_name":user_name,"withSafetyModeUserFields":True,"withSuperFollowsUserFields":True}),
            'features': json.dumps({"responsive_web_graphql_timeline_navigation_enabled":False})
        }
        return self.__get(url, params)
    
    def get_user_timeline(self, uid):
        url = 'https://twitter.com/i/api/graphql/edn8-AOJHq7gBM6OPpWT_g/UserTweets'
        params = {
            'variables': json.dumps({"userId":uid,"count":40,"includePromotedContent":True,"withQuickPromoteEligibilityTweetFields":True,"withSuperFollowsUserFields":True,"withDownvotePerspective":False,"withReactionsMetadata":False,"withReactionsPerspective":False,"withSuperFollowsTweetFields":True,"withVoice":True,"withV2Timeline":True}),
            'features': json.dumps({"responsive_web_graphql_timeline_navigation_enabled":False,"unified_cards_ad_metadata_container_dynamic_card_content_query_enabled":True,"responsive_web_uc_gql_enabled":True,"vibe_api_enabled":True,"responsive_web_edit_tweet_api_enabled":True,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":False,"standardized_nudges_misinfo":True,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":False,"interactive_text_enabled":True,"responsive_web_text_conversations_enabled":False,"responsive_web_enhance_cards_enabled":True})
        }
        return self.__get(url, params)
    
    def get_tweet_detail(self, tid):
        url = 'https://twitter.com/i/api/graphql/zZXycP0V6H7m-2r0mOnFcA/TweetDetail'
        params = {
            'variables': json.dumps({"focalTweetId":tid,"with_rux_injections":False,"includePromotedContent":True,"withCommunity":True,"withQuickPromoteEligibilityTweetFields":True,"withBirdwatchNotes":False,"withSuperFollowsUserFields":True,"withDownvotePerspective":False,"withReactionsMetadata":False,"withReactionsPerspective":False,"withSuperFollowsTweetFields":True,"withVoice":True,"withV2Timeline":True}),
            'features': json.dumps({"verified_phone_label_enabled":False,"responsive_web_graphql_timeline_navigation_enabled":False,"unified_cards_ad_metadata_container_dynamic_card_content_query_enabled":True,"tweetypie_unmention_optimization_enabled":True,"responsive_web_uc_gql_enabled":True,"vibe_api_enabled":True,"responsive_web_edit_tweet_api_enabled":True,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":False,"standardized_nudges_misinfo":True,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":False,"interactive_text_enabled":True,"responsive_web_text_conversations_enabled":False,"responsive_web_enhance_cards_enabled":True})
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
        legacy = user_result['legacy']
        user_info = dict(
            id=user_result['rest_id'],
            name=legacy['name'],
            location=legacy['location'],
            description=legacy['description'],
            followers_count=legacy['followers_count'],
            following_count=legacy['friends_count'],
            icon=legacy['profile_image_url_https']
        )
        return user_info
    
    @staticmethod
    def parse_timeline(timeline):
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
    # res = tm.get_user_info('gume0612')
    # print(res.status_code, res.json())
    # res = res.json()
    # print(tm.parse_user_info(res))
    # uid = res['data']['user']['result']['rest_id']
    # res = tm.get_user_timeline(uid)
    # print(res.status_code, res.json())
    # print(tm.parse_timeline(res.json()))
    res = tm.get_tweet_detail('1675777787368722433')
    # print(res.status_code, res.json())
    tdata, user_info = tm.parse_tweet_detail(res.json())
    tweet_type = tdata['tweet_type']
    if tweet_type == 'default':
        imgs = tdata.get('imgs')
    elif tweet_type == 'retweet':
        retweet_data = tdata['retweet_data']
        imgs = retweet_data['data'].get('imgs')
    elif tweet_type == 'quote':
        quote_data = tdata['quote_data']
        imgs = quote_data['data'].get('imgs')
    print(tdata)
    if imgs:
        print(imgs)
