#!/usr/bin/env python3
"""
Signal Storm - 最终解密
密钥: C0lm_be4ore_7he_st0rm (21字节)
"""

# 加密数据
encrypted = bytes([
    0xe3, 0x36, 0xd9, 0xc8, 0xc9, 0xc1, 0x60, 0x82,
    0x75, 0xd9, 0x11, 0x25, 0xd5, 0xb2, 0x4b, 0x1c,
    0x4d, 0xe6, 0x6d, 0x71, 0x1c, 0xaf, 0x1c, 0xf1,
    0x06, 0xa5, 0x1c, 0x26, 0x7f, 0xf6, 0x5a, 0x1a
])

# 发现的密钥
key = b"C0lm_be4ore_7he_st0rm"

print(f"密钥: {key}")
print(f"密钥长度: {len(key)}")

def rc4_decrypt(key_bytes, data):
    # KSA
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key_bytes[i % len(key_bytes)]) % 256
        S[i], S[j] = S[j], S[i]
    
    # PRGA
    i = j = 0
    result = []
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        result.append(byte ^ k)
    return bytes(result)

# 解密
flag = rc4_decrypt(key, encrypted)
print(f"\n=== FLAG ===")
print(f"{flag.decode()}")
