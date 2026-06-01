import requests

# 目标URL
base_url = "http://dc380860.clsadp.com"

# 创建会话
session = requests.Session()

# 常见的若依路径
paths_to_try = [
    "/",
    "/index",
    "/login",
    "/system",
    "/tool",
    "/tool/gen",
    "/tool/gen/list",
    "/tool/gen/db/list",
    "/tool/gen/createTable",
    "/tool/gen/importTable",
    "/tool/gen/preview/1",
    "/api",
    "/admin",
    "/generator",
    "/gen",
    "/gen/list",
    "/gen/createTable",
    "/createTable",
    "/shopayouwei",
]

print("[*] 扫描可能的路径...")
for path in paths_to_try:
    try:
        response = session.get(f"{base_url}{path}", timeout=5, allow_redirects=False)
        status = response.status_code
        length = len(response.content)
        
        # 只显示非404的响应
        if status != 404:
            print(f"[+] {path:30s} - 状态码: {status} - 长度: {length}")
            
            # 如果是200,显示前100字符
            if status == 200:
                preview = response.text[:150].replace('\n', ' ')
                print(f"    内容: {preview}")
            
    except Exception as e:
        print(f"[-] {path:30s} - 错误: {e}")

# 尝试POST请求
print("\n[*] 尝试POST请求...")
post_paths = [
    "/tool/gen/list",
    "/tool/gen/createTable",
    "/gen/list",
    "/gen/createTable",
    "/createTable",
]

for path in post_paths:
    try:
        response = session.post(f"{base_url}{path}", data={}, timeout=5)
        status = response.status_code
        length = len(response.content)
        
        if status != 404:
            print(f"[+] POST {path:25s} - 状态码: {status} - 长度: {length}")
            if status == 200 or status == 500:
                preview = response.text[:150].replace('\n', ' ')
                print(f"    内容: {preview}")
            
    except Exception as e:
        pass  # 忽略错误

print("\n[*] 扫描完成")
