import requests

base_url = "http://dc380860.clsadp.com"

# CONNECT返回200，让我详细测试
print("[*] 详细测试CONNECT方法...")
try:
    response = requests.request("CONNECT", f"{base_url}/shopayouwei", timeout=5)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容长度: {len(response.content)}")
    print(f"响应内容: '{response.text}'")
    print(f"原始内容: {response.content}")
except Exception as e:
    print(f"错误: {e}")

# 尝试其他不常见的HTTP方法
print("\n[*] 尝试其他不常见的HTTP方法...")
uncommon_methods = ["PROPFIND", "PROPPATCH", "MKCOL", "COPY", "MOVE", "LOCK", "UNLOCK", "SEARCH"]
for method in uncommon_methods:
    try:
        response = requests.request(method, f"{base_url}/shopayouwei", timeout=5)
        if response.status_code != 403 and response.status_code != 404 and response.status_code != 405:
            print(f"[+] {method:12s} - {response.status_code} - {len(response.content)} bytes")
            if len(response.content) > 0:
                print(f"    {response.text[:100]}")
    except:
        pass

# 尝试用CONNECT访问其他路径
print("\n[*] 用CONNECT方法访问其他路径...")
paths = ["/", "/flag", "/admin", "/api", "/tool/gen/createTable"]
for path in paths:
    try:
        response = requests.request("CONNECT", f"{base_url}{path}", timeout=5)
        if response.status_code == 200:
            print(f"[+] CONNECT {path:30s} - {response.status_code} - {len(response.content)} bytes")
    except:
        pass

print("\n[*] 测试完成")
