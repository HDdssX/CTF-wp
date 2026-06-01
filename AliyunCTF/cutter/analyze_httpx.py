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
body = req.content
print(body.decode('utf-8', errors='replace'))
print("\n=== Body Length ===", len(body))
