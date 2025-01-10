import traceback
from googleapiclient.discovery import build

from botoy import jconfig

class YoutubeManager():
    def __init__(self):
        youtube_conf = jconfig.get_configuration('youtube')
        
        self.youtube = build('youtube', 'v3', developerKey=youtube_conf.get('api_key'))

    def get_channel_id(self, handle: str):
        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                forUsername=handle
            )
            response = request.execute()
            print(response)
            return 0, response['items'][0]['id']
        except Exception as e:
            traceback.print_exc()
            return 500, traceback.format_exc()
        
    def check_live_stream(self, channel_id: str):
        try:
            request = self.youtube.search().list(
                part="snippet",
                channelId=channel_id,
                eventType="live",
                type="video"
            )
            response = request.execute()
            if not response['items']:
                return 0, {}
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