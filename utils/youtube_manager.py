import traceback
from googleapiclient.discovery import build

from botoy import jconfig

class YoutubeManager():
    def __init__(self):
        youtube_conf = jconfig.get_configuration('youtube')
        
        self.youtube = build('youtube', 'v3', developerKey=youtube_conf.get('api_key'))

    def get_playlist_id(self, user_id: str, id_type: str):
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
            return 0, response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
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
            if not response['items']:
                return 0, {'name': 'none', 'liveBroadcastContent': 'none'}
            for i in response['items']:
                if i['snippet']['liveBroadcastContent'] in ['live', 'upcoming']:
                    break
            else:
                i = response['items'][0]
            res = {'liveStreamingDetails': i['liveStreamingDetails']}
            res_row = i['snippet']
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