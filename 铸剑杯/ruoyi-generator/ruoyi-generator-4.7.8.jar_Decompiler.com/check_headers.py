import requests

base_url = "http://dc380860.clsadp.com"

# 查看所有响应头
paths = ["/", "/shopayouwei"]

for path in paths:
    try:
        response = requests.get(f"{base_url}{path}", timeout=5)
        print(f"\n[*] 路径: {path}")
        print(f"    状态码: {response.status_code}")
        print(f"    响应头:")
        for key, value in response.headers.items():
            print(f"      {key}: {value}")
        
        # 查看是否有Set-Cookie
        if 'Set-Cookie' in response.headers:
            print(f"    [!] 发现Set-Cookie: {response.headers['Set-Cookie']}")
            
    except Exception as e:
        print(f"[-] {path} 错误: {e}")

# 尝试OPTIONS请求看看支持什么方法
print("\n[*] 尝试OPTIONS请求...")
for path in ["/", "/shopayouwei"]:
    try:
        response = requests.options(f"{base_url}{path}", timeout=5)
        print(f"    {path}: {response.status_code}")
        if 'Allow' in response.headers:
            print(f"      允许的方法: {response.headers['Allow']}")
    except:
        pass
