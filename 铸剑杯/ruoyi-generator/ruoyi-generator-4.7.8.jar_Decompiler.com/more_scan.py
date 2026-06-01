import requests

base_url = "http://dc380860.clsadp.com"
session = requests.Session()

# 歌词相关的路径
print("[*] 尝试歌词相关路径...")
paths = [
    "/买不回",  
    "/buyback",
    "/mai不hui",
    "/回不来",
    "/buynotback",
    "/0yuan",
    "/0元购",
    "/freeshop",
]

for path in paths:
    try:
        response = session.get(f"{base_url}{path}", timeout=5)
        if response.status_code != 404:
            print(f"[+] {path:20s} - {response.status_code}")
    except:
        pass

# 题目提到了若依代码生成器，但目前没找到相关接口
# 让我尝试寻找可能的API模式
print("\n[*] 尝试RESTful API模式...")
rest_paths = [
    "/api/tool/gen/createTable",
    "/api/tool/gen/list",
    "/api/gen/createTable",
    "/v1/gen/createTable",
    "/api/v1/gen/createTable",
]

for path in rest_paths:
    try:
        # GET
        response = session.get(f"{base_url}{path}", timeout=5)
        if response.status_code != 404:
            print(f"[+] GET  {path:30s} - {response.status_code}")
        
        # POST
        response = session.post(f"{base_url}{path}", json={}, timeout=5)
        if response.status_code != 404:
            print(f"[+] POST {path:30s} - {response.status_code}")
            if response.status_code == 200 or response.status_code == 500:
                print(f"     {response.text[:150]}")
    except:
        pass

# 尝试访问根路径后带不同的query参数
print("\n[*] 尝试query参数...")
query_tests = [
    "/?page=shopayouwei",
    "/?path=shopayouwei",
    "/?action=shopayouwei",
    "/?cmd=shopayouwei",
    "/?debug=1",
    "/?admin=1",
]

for query in query_tests:
    try:
        response = session.get(f"{base_url}{query}", timeout=5)
        if len(response.content) != 11748:  # 主页的长度
            print(f"[+] {query:30s} - {response.status_code} - {len(response.content)} bytes")
    except:
        pass

print("\n[*] 测试完成")
