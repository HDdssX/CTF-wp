#!/usr/bin/env python3
"""
Signal Storm - 完整分析与解密
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

# 标准 RC4 解密
flag = rc4_decrypt(key, encrypted)
print(f"标准 RC4: {flag}")

# 程序中的加密更复杂，包含信号处理的特殊逻辑
# 让我模拟完整流程

print("\n=== 模拟信号处理加密 ===")

# 全局状态
S = list(range(256))  # S-box
key_array = list(key)  # 密钥数组
idx = 0
j = 0

# KSA - 初始化 S-box
for i in range(256):
    j = (j + S[i] + key_array[i % len(key_array)]) % 256
    S[i], S[j] = S[j], S[i]

print(f"KSA 后 S-box 前16字节: {S[:16]}")

# 重置 PRGA 状态
idx = 0
j = 0

# 模拟信号处理加密流程
result = []
for pos in range(32):
    # SIGSEGV handler: 交换
    idx = (idx + 1) % 256
    tmp = S[idx]
    j = (j + tmp + key_array[idx % 21]) % 256
    S[idx], S[j] = S[j], S[idx]
    
    # SIGFPE handler: XOR
    k = S[(S[idx] + S[j]) % 256]
    result.append(encrypted[pos] ^ k)
    
    # SIGTRAP handler: 密钥旋转
    first = key_array[0]
    key_array = key_array[1:] + [first]

print(f"信号处理解密: {bytes(result)}")

# 分析：在 PRGA 过程中，密钥也参与了 j 的计算
# 并且密钥每轮都会旋转

# 为了解密，我们需要逆向这个过程
# 但 RC4 是对称的，所以相同的加密过程应该能解密

print("\n=== 尝试不同的 KSA + 信号处理组合 ===")

# 重新初始化
key_array = list(key)
S = list(range(256))
j = 0

# 标准 KSA
for i in range(256):
    j = (j + S[i] + key_array[i % len(key_array)]) % 256
    S[i], S[j] = S[j], S[i]

# PRGA 不使用密钥参与 j 计算
idx = 0
j = 0
result = []
for byte in encrypted:
    idx = (idx + 1) % 256
    j = (j + S[idx]) % 256
    S[idx], S[j] = S[j], S[idx]
    k = S[(S[idx] + S[j]) % 256]
    result.append(byte ^ k)

print(f"标准 PRGA: {bytes(result)}")

# 再试试：KSA 后不重置 j
print("\n=== KSA 后不重置 j ===")

key_array = list(key)
S = list(range(256))
j = 0

for i in range(256):
    j = (j + S[i] + key_array[i % len(key_array)]) % 256
    S[i], S[j] = S[j], S[i]

# j 保持 KSA 结束时的值
idx = 0
result = []
for byte in encrypted:
    idx = (idx + 1) % 256
    j = (j + S[idx]) % 256
    S[idx], S[j] = S[j], S[idx]
    k = S[(S[idx] + S[j]) % 256]
    result.append(byte ^ k)

print(f"不重置j: {bytes(result)}")

# 让我检查一下程序中 PRGA 的确切逻辑
print("\n=== 分析 PRGA 中的密钥使用 ===")

# 从 SIGSEGV handler (0x1640) 分析:
# idx = (idx + 1) % 256
# tmp = S[idx]
# j = (j + tmp + key[idx % 21]) % 256  <- 关键：这里使用了密钥！
# swap(S[idx], S[j])

# 这意味着在 PRGA 阶段，密钥也被使用
# 而且 SIGTRAP 会旋转密钥

# 正确的解密流程
print("\n=== 正确的解密流程 ===")

# 初始化
key_array = list(key)
S = list(range(256))
j = 0

# KSA
for i in range(256):
    j = (j + S[i] + key_array[i % len(key_array)]) % 256
    S[i], S[j] = S[j], S[i]

# 重置状态
idx = 0
j = 0
key_array = list(key)  # 重新初始化密钥数组

result = bytearray(encrypted)

# PRGA with key rotation
for pos in range(32):
    # SIGSEGV: 使用密钥参与 j 计算
    idx = (idx + 1) % 256
    j = (j + S[idx] + key_array[idx % 21]) % 256
    S[idx], S[j] = S[j], S[idx]
    
    # SIGFPE: XOR
    k = S[(S[idx] + S[j]) % 256]
    result[pos] ^= k
    
    # SIGTRAP: 密钥左旋转
    first = key_array[0]
    key_array = key_array[1:] + [first]

print(f"完整流程解密: {bytes(result)}")

# 检查是否 hgame 格式
try:
    decoded = bytes(result).decode('ascii')
    print(f"ASCII: {decoded}")
except:
    print(f"无法解码为 ASCII: {bytes(result).hex()}")

# 再分析：程序验证时用的是比较
# 0x14b5-0x153c 处的比较逻辑
# 它比较 input[0:8] 和 input[8:16] 以及 input[16:24] 和 input[24:32]
# 与常量值

# 这说明加密后的数据应该等于 encrypted
# 所以用户输入的明文经过上述变换后 == encrypted
# 我们需要解密 encrypted 得到明文

print("\n=== 暴力搜索密钥变体 ===")

# 可能需要尝试不同的密钥用法
test_variants = [
    (True, True, True),   # KSA用密钥, PRGA用密钥, 旋转密钥
    (True, True, False),  # KSA用密钥, PRGA用密钥, 不旋转
    (True, False, True),  # KSA用密钥, PRGA不用密钥, 旋转
    (True, False, False), # 标准RC4
    (False, True, True),  # KSA不用密钥, PRGA用密钥, 旋转
]

for use_key_ksa, use_key_prga, rotate_key in test_variants:
    key_array = list(key)
    S = list(range(256))
    j = 0
    
    # KSA
    for i in range(256):
        if use_key_ksa:
            j = (j + S[i] + key_array[i % len(key_array)]) % 256
        else:
            j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
    
    # Reset
    idx = 0
    j = 0
    key_array = list(key)
    
    result = bytearray(encrypted)
    
    for pos in range(32):
        idx = (idx + 1) % 256
        if use_key_prga:
            j = (j + S[idx] + key_array[idx % 21]) % 256
        else:
            j = (j + S[idx]) % 256
        S[idx], S[j] = S[j], S[idx]
        k = S[(S[idx] + S[j]) % 256]
        result[pos] ^= k
        
        if rotate_key:
            first = key_array[0]
            key_array = key_array[1:] + [first]
    
    try:
        decoded = bytes(result).decode('ascii')
        if decoded.startswith('hgame{') or decoded.startswith('flag{') or all(32 <= b <= 126 for b in result):
            print(f"KSA={use_key_ksa}, PRGA={use_key_prga}, Rotate={rotate_key}: {decoded}")
    except:
        pass
