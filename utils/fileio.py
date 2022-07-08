import json
import base64

def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)
    
def write_json(path, d):
    with open(path, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
    
def write_pic(path, img_data):
    with open(path, 'wb') as f:
        f.write(img_data)
    
def picToBase64(pic_path):
    with open(pic_path, 'rb') as f:
        pic = f.read()
    return str(base64.b64encode(pic), encoding = 'utf-8')