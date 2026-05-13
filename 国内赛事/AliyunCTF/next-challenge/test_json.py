#!/usr/bin/env python3
import json

# 测试 JSON 中的 Unicode 转义
# JSON: ["\u0063onstructor"] 
# 这在JSON中表示字符串 "constructor"

json_str = '["\\u0063onstructor"]'
print(f"JSON string: {repr(json_str)}")

parsed = json.loads(json_str)
print(f"Parsed: {repr(parsed)}")
print(f"First element: {repr(parsed[0])}")
print(f"'constructor' in value.lower(): {'constructor' in parsed[0].lower()}")

print()

# WAF 检查的是 PARSED 后的值！
# 所以 \u0063 会被解码成 c，然后整个字符串是 "constructor"
# WAF 检查 "constructor" in "constructor".lower() -> True -> BLOCKED

# 那 \\u 呢？
# JSON: ["\\u0063"] 表示字符串 "\u0063" (4个字符)
json_str2 = '["\\\\u0063"]'
print(f"JSON string 2: {repr(json_str2)}")
parsed2 = json.loads(json_str2)
print(f"Parsed 2: {repr(parsed2)}")
print(f"'\\\\u' in value: {'\\u' in parsed2[0]}")

# 所以如果我们发送 \\u，WAF会检测到 \u -> BLOCKED
