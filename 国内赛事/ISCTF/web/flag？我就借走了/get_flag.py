import requests

base_url = "http://challenge.bluesharkinfo.com:21565"

# 尝试下载flag_link
print("[*] 尝试访问 /download/flag_link")
response = requests.get(f"{base_url}/download/flag_link")
print(f"状态码: {response.status_code}")
print(f"内容: {response.text}")
print()

# 尝试不同的路径
paths = [
    "/download/flag_link",
    "/download/flag_link/",
    "/files/flag_link",
    "/static/flag_link",
]

for path in paths:
    print(f"[*] 尝试访问: {path}")
    try:
        response = requests.get(f"{base_url}{path}")
        if response.status_code == 200:
            print(f"  状态码: {response.status_code}")
            print(f"  内容: {response.text}")
            if 'flag' in response.text.lower() or 'isctf' in response.text.lower():
                print(f"\n[+] 可能找到flag: {response.text}")
        elif response.status_code != 404:
            print(f"  状态码: {response.status_code}")
    except Exception as e:
        print(f"  错误: {e}")
    print()
