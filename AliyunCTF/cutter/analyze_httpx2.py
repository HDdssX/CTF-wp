import httpx
from io import BytesIO

# 模拟 heartbeat 中的请求构造
text = "TEST_CONTENT"
action = '{"type": "echo"}'

form_data = {
    'content': ('content', BytesIO(text.encode()), 'text/plain'),
    'action' : ('action', BytesIO(action.encode()), 'text/json')
}

headers = {
    "X-Token": "fake_token",
}
headers["X-Custom"] = "custom_value"

# 创建一个请求看看原始格式
req = httpx.Request(
    "POST",
    "http://127.0.0.1:5000/action",
    headers=headers,
    files=form_data
)

print("=== Headers ===")
for k, v in req.headers.items():
    print(f"{k}: {v}")

print("\n=== Body ===")
req.read()  # 需要先读取
body = req.content
print(body.decode('utf-8', errors='replace'))
print("\n=== Body Length ===", len(body))

# 现在测试当我们覆盖 Content-Type 时会发生什么
print("\n\n=== Test with custom Content-Type ===")
headers2 = {
    "X-Token": "fake_token",
    "Content-Type": "multipart/form-data; boundary=CUSTOM_BOUNDARY"
}

req2 = httpx.Request(
    "POST",
    "http://127.0.0.1:5000/action",
    headers=headers2,
    files=form_data
)

print("=== Headers ===")
for k, v in req2.headers.items():
    print(f"{k}: {v}")

form_data2 = {
    'content': ('content', BytesIO(text.encode()), 'text/plain'),
    'action' : ('action', BytesIO(action.encode()), 'text/json')
}
req2 = httpx.Request(
    "POST",
    "http://127.0.0.1:5000/action",
    headers=headers2,
    files=form_data2
)
req2.read()
print("\n=== Body ===")
print(req2.content.decode('utf-8', errors='replace'))
