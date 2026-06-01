import httpx

# 测试 httpx 对特殊 header 名称的处理
special_headers = [
    ("Content-Length", "999"),  # 可能导致 request smuggling
    ("Transfer-Encoding", "chunked"),  # 可能导致 request smuggling
    ("Host", "evil.com"),  # Host 头注入
    ("Content-Type", "text/html"),  # 改变 content type
    ("X-Custom\r\nX-Injected", "value"),  # CRLF in header name
]

for header_name, header_value in special_headers:
    print(f"\nTesting header: {header_name}: {header_value}")
    try:
        headers = {"X-Test": "value"}
        headers[header_name] = header_value
        
        req = httpx.Request(
            "POST",
            "http://127.0.0.1:5000/test",
            headers=headers,
            content=b"test"
        )
        print(f"  Request headers: {dict(req.headers)}")
    except Exception as e:
        print(f"  Error: {e}")

# 测试重复的 Content-Type
print("\n\nTesting duplicate Content-Type...")
try:
    headers = {
        "Content-Type": "text/plain",
    }
    req = httpx.Request(
        "POST",
        "http://127.0.0.1:5000/test",
        headers=headers,
        files={"file": ("test.txt", b"content", "application/json")}
    )
    req.read()
    print(f"Headers after files: {dict(req.headers)}")
except Exception as e:
    print(f"Error: {e}")
