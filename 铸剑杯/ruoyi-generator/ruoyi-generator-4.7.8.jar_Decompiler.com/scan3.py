import requests

base_url = "http://dc380860.clsadp.com"
session = requests.Session()

# shopayouwei的各种变化
print("[*] 尝试shopayouwei的变种...")
paths = [
    "/shopayouwei",
    "/shopayouwei/",
    "/shopayouwei/index",
    "/shopayouwei/home",
    "/shopayouwei/admin",
    "/shopayouwei/flag",
    "/shopayouwei/generator",
    "/shopayouwei/gen",
    "/shopayouwei/tool",
    "/shopayouwei/tool/gen",
    "/shopayouwei/tool/gen/createTable",
    "/shopayouwei/createTable",
    "/tool/gen/createTable",
    "/gen/createTable",
]

for path in paths:
    try:
        # GET请求
        response = session.get(f"{base_url}{path}", timeout=5)
        if response.status_code != 404:
            print(f"[+] GET  {path:40s} - {response.status_code}")
            if response.status_code == 200:
                print(f"     {response.text[:100]}")
        
        # POST请求
        response = session.post(f"{base_url}{path}", data={}, timeout=5)
        if response.status_code != 404:
            print(f"[+] POST {path:40s} - {response.status_code}")
            if response.status_code == 200:
                print(f"     {response.text[:100]}")
    except:
        pass

# 尝试直接访问可能的接口
print("\n[*] 尝试直接调用API接口...")
api_tests = [
    ("POST", "/createTable", {"sql": "CREATE TABLE test (id INT)"}),
    ("POST", "/gen/createTable", {"sql": "CREATE TABLE test (id INT)"}),
    ("POST", "/tool/gen/createTable", {"sql": "CREATE TABLE test (id INT)"}),
    ("GET", "/preview/1", {}),
    ("GET", "/gen/preview/1", {}),
    ("GET", "/tool/gen/preview/1", {}),
]

for method, path, data in api_tests:
    try:
        if method == "POST":
            response = session.post(f"{base_url}{path}", data=data, timeout=5)
        else:
            response = session.get(f"{base_url}{path}", params=data, timeout=5)
        
        if response.status_code != 404:
            print(f"[+] {method} {path:35s} - {response.status_code}")
            print(f"     {response.text[:150]}")
    except:
        pass

print("\n[*] 扫描完成")
