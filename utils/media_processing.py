''' 媒体文件处理 '''
import requests
import base64

def download_from_url_and_convert_to_base64(url):
    response = requests.get(url)
    if response.status_code == 200:
        image_base64 = base64.b64encode(response.content).decode()
        return 200, image_base64
    else:
        print("下载失败，状态码:", response.status_code)
        return response.status_code, response.text