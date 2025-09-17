import requests
import re

base_url = "http://dc380860.clsadp.com"
session = requests.Session()

# 密码从HTML中得知是123456
print("[*] 尝试登录...")
# 但JavaScript只验证密码，并没有提交到后端

# 让我尝试一些Flask/Python后端的常见路径
print("\n[*] 尝试Python Flask常见路径...")
flask_paths = [
    "/api",
    "/api/v1",
    "/flag",
    "/admin",
    "/debug",
    "/console",
    "/shop",
    "/gen",
    "/generator",
    "/create",
    "/preview",
    "/download",
    "/upload",
]

for path in flask_paths:
    try:
        response = session.get(f"{base_url}{path}", timeout=5)
        if response.status_code != 404:
            print(f"[+] {path:20s} - {response.status_code} - {len(response.content)} bytes")
            if response.status_code == 200:
                print(f"    {response.text[:100]}")
    except:
        pass

# 尝试带参数的路径
print("\n[*] 尝试带参数的路径...")
param_paths = [
    "/preview?id=1",
    "/download?file=flag",
    "/api/flag",
    "/api/preview",
    "/shopayouwei?debug=1",
    "/shopayouwei/admin",
    "/shopayouwei/flag",
]

for path in param_paths:
    try:
        response = session.get(f"{base_url}{path}", timeout=5)
        if response.status_code != 404:
            print(f"[+] {path:30s} - {response.status_code} - {len(response.content)} bytes")
    except:
        pass

# 尝试查看静态资源目录
print("\n[*] 尝试访问静态资源...")
static_paths = [
    "/static",
    "/static/",
    "/static/css",
    "/static/js",
    "/templates",
]

for path in static_paths:
    try:
        response = session.get(f"{base_url}{path}", timeout=5)
        if response.status_code != 404:
            print(f"[+] {path:20s} - {response.status_code} - {len(response.content)} bytes")
            if response.status_code == 200 or response.status_code == 403:
                print(f"    {response.text[:200]}")
    except:
        pass

print("\n[*] 扫描完成")
