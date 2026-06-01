import requests

# 尝试访问config.php
config_url = "http://f7c8a2a3.clsadp.com/config.php"

print("Checking config.php...")
response = requests.get(config_url, timeout=10)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)}")
print(f"Content:\n{response.text}\n")

# 新思路：也许我们可以让$this->username指向一个能读取文件并在destruct时输出的对象？
# 但由于install.lock存在，destruct会early exit...

# 或者，我们可以尝试删除install.lock?
# 但没有删除文件的原生类方法...

# 让我尝试其他方法 - 直接访问可能的flag文件位置
flag_urls = [
    "http://f7c8a2a3.clsadp.com/flag",
    "http://f7c8a2a3.clsadp.com/flag.txt",
    "http://f7c8a2a3.clsadp.com/flag.php",
    "http://f7c8a2a3.clsadp.com/f1ag",
    "http://f7c8a2a3.clsadp.com/fl4g",
]

print("\n" + "="*70)
print("Trying direct access to flag files...")
print("="*70)

for url in flag_urls:
    try:
        r = requests.get(url, timeout=10)
        print(f"\n{url}")
        print(f"Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200 and len(r.text) < 1000:
            print(f"Content: {r.text}")
    except:
        pass
