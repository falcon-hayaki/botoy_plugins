import traceback
from googleapiclient.discovery import build

from botoy import jconfig

class YoutubeManager():
    def __init__(self):
        youtube_conf = jconfig.get_configuration('youtube')
        
        self.youtube = build('youtube', 'v3', developerKey=youtube_conf.get('api_key'))

    def get_channel_details(self, user_id: str, id_type: str):
        try:
            if id_type == 'handle':
                request = self.youtube.channels().list(
                    part="snippet,contentDetails,statistics",
                    forHandle=user_id
                )
            elif id_type == 'id':
                request = self.youtube.channels().list(
                    part="snippet,contentDetails,statistics",
                    id=user_id
                )
            response = request.execute()
            return 0, response['items'][0]
        except Exception as e:
            traceback.print_exc()
            return 500, traceback.format_exc()
        
    def get_playlist_video_ids(self, playlist_id: str):
        try:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=5
            )
            response = request.execute()
            res = [i['contentDetails']['videoId'] for i in response['items']]
            return 0, res
        except Exception as e:
            traceback.print_exc()
            return 500, traceback.format_exc()
        
    def check_live_stream(self, video_id_list: list):
        try:
            request = self.youtube.videos().list(
                part="snippet,liveStreamingDetails",
                id=','.join(video_id_list)
            )
            response = request.execute()
            res = {
                'live': {},
                'upcoming': {}
            }
            if not response['items']:
                return 0, res
            for i in response['items']:
                if i['snippet']['liveBroadcastContent'] in ['live', 'upcoming']:
                    res_one = {
                        'liveStreamingDetails': i.get('liveStreamingDetails', {}),
                        'name': i['snippet']['channelTitle'],
                        'title': i['snippet']['title'],
                        'description': i['snippet']['description'],
                        'liveBroadcastContent': i['snippet']['liveBroadcastContent'],
                        'publishedAt': i['snippet']['publishedAt'],
                        'thumbnail': i['snippet']['thumbnails'].get('high', i['snippet']['thumbnails'].get('medium', i['snippet']['thumbnails'].get('default', {})))['url']
                    }
                    res[i['snippet']['liveBroadcastContent']][i['id']] = res_one
            return 0, res
        except Exception as e:
            traceback.print_exc()
            return 500, traceback.format_exc()
        
    def get_video_details(self, video_id: str):
        try:
            request = self.youtube.videos().list(
                part="snippet",
                id=video_id
            )
            response = request.execute()
            res = {}
            res_row = response['items'][0]['snippet']
            res['name'] = res_row['channelTitle']
            res['title'] = res_row['title']
            res['description'] = res_row['description']
            res['liveBroadcastContent'] = res_row['liveBroadcastContent']
            res['publishedAt'] = res_row['publishedAt']
            res['thumbnail'] = res_row['thumbnails'].get('high', res_row['thumbnails'].get('medium', res_row['thumbnails'].get('default', {})))['url']
            return 0, res
        except Exception as e:
            traceback.print_exc()
            return 500, traceback.format_exc()

if __name__ == "__main__":
    pass