#!/usr/bin/env python3
# Signal Storm - CTF Reverse Solution
# 分析：程序使用 RC4 算法加密，通过信号处理实现加密逻辑

# 从 .rodata 段提取的加密数据 (地址 0x20a0)
encrypted = bytes([
    0xe3, 0x36, 0xd9, 0xc8, 0xc9, 0xc1, 0x60, 0x82,
    0x75, 0xd9, 0x11, 0x25, 0xd5, 0xb2, 0x4b, 0x1c,
    0x4d, 0xe6, 0x6d, 0x71, 0x1c, 0xaf, 0x1c, 0xf1,
    0x06, 0xa5, 0x1c, 0x26, 0x7f, 0xf6, 0x5a, 0x1a
])

# RC4 密钥（从 0x4010 位置读取的21字节，用于初始化S盒）
# 根据反汇编分析，密钥是21字节（0x15）
key = bytes([0] * 21)  # 初始密钥全为0

def rc4_init(key):
    """RC4 初始化 S盒"""
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    return S

def rc4_crypt(S, data):
    """RC4 加解密"""
    S = S.copy()
    result = []
    i = j = 0
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        result.append(byte ^ k)
    return bytes(result)

# 尝试使用空密钥解密
S = rc4_init(key)
decrypted = rc4_crypt(S, encrypted)
print(f"尝试空密钥解密: {decrypted}")

# 从代码分析，程序还有一个反调试函数读取 /proc/self/status 的 TracerPid
# 获取的值会XOR到某个缓冲区，如果被调试，值不为0

# 但关键是 main 函数开头调用的初始化函数 (0x1780)
# 它用一个固定的 21 字节密钥来初始化 S 盒

# 再次分析代码，发现地址 0x4010 的数据被用作密钥
# 而该数据在 .rodata 中显示为全0

# 让我直接用 RC4 标准算法，假设密钥就是全0的21字节
print("\n分析 RC4 算法...")

# 重新分析：密钥长度是 0x15 = 21
# S盒初始化和KSA（密钥调度算法）
# PRGA（伪随机生成算法）用于生成密钥流

# 从初始化函数 0x1780 分析：
# - 初始化 S[0..255] = 0,1,2,...,255
# - 使用某个固定密钥进行KSA

# 根据程序逻辑，这实际上是一个标准 RC4
S = list(range(256))
j = 0
# 空密钥 KSA
for i in range(256):
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]

# PRGA 解密
result = []
i = j = 0
for byte in encrypted:
    i = (i + 1) % 256
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]
    k = S[(S[i] + S[j]) % 256]
    result.append(byte ^ k)

print(f"RC4空密钥解密: {bytes(result)}")

# 重新仔细分析汇编代码...
# 在 0x12c0 处有一个循环，用某个值 XOR 数据
# 这个值来自 /proc/self/status 中的 TracerPid

# 程序正常运行时 TracerPid = 0
# 所以 XOR 操作对数据没有影响

# 关键在于 0x1780 处的 S 盒初始化
# 它使用 .rodata 中的 constant 表来初始化

# 让我重新分析初始化逻辑
print("\n重新分析 RC4 S盒初始化...")

# 从 0x20d0 开始的数据用于初始化
init_data = [
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 
    0x02, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00,  # 0x20d0
    0x10, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 
    0x10, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00,  # 0x20e0
    0x04, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 
    0x04, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00,  # 0x20f0
    0x08, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 
    0x08, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00,  # 0x2100
    0x0c, 0x00, 0x00, 0x00, 0x0c, 0x00, 0x00, 0x00, 
    0x0c, 0x00, 0x00, 0x00, 0x0c, 0x00, 0x00, 0x00,  # 0x2110
    0xff, 0x00, 0xff, 0x00, 0xff, 0x00, 0xff, 0x00, 
    0xff, 0x00, 0xff, 0x00, 0xff, 0x00, 0xff, 0x00,  # 0x2120
]

# 标准 RC4，密钥为全0
# S 盒初始化为 0,1,2...255
# KSA 用密钥打乱 S 盒
# PRGA 生成密钥流

# 根据代码分析，密钥从 0x4010 位置读取
# 该位置存储的是21字节数据

# 在 0x4010 存储的数据在运行时被修改
# 初始值需要从二进制分析

# 让我换一种方法：直接穷举简单密钥
print("\n尝试直接分析...")

# 从代码流程看：
# 1. 初始化 S 盒 (0x1780)
# 2. 循环32次，每次通过信号触发加密操作
# 3. 最终比较结果

# 信号处理器:
# - SIGSEGV (11/0x0b): 交换 S 盒元素
# - SIGFPE (8): XOR 解密当前字节
# - SIGTRAP (5): 旋转密钥数组

# 这实际上是一个变种 RC4
# 让我模拟信号处理流程

def signal_storm_decrypt():
    # 初始化 S 盒
    S = list(range(256))
    
    # 密钥数组（21字节，初始为0）
    key = [0] * 21
    
    # 状态变量
    idx = 0  # S盒索引
    j = 0    # 累加器
    
    # KSA (Key Scheduling Algorithm)
    for i in range(256):
        idx = (idx + 1) % 256
        j = (j + S[idx] + key[idx % 21]) % 256
        S[idx], S[j] = S[j], S[i]
    
    # 重置状态用于 PRGA
    i = j = 0
    
    # 存储输入的缓冲区
    encrypted = bytes([
        0xe3, 0x36, 0xd9, 0xc8, 0xc9, 0xc1, 0x60, 0x82,
        0x75, 0xd9, 0x11, 0x25, 0xd5, 0xb2, 0x4b, 0x1c,
        0x4d, 0xe6, 0x6d, 0x71, 0x1c, 0xaf, 0x1c, 0xf1,
        0x06, 0xa5, 0x1c, 0x26, 0x7f, 0xf6, 0x5a, 0x1a
    ])
    
    result = []
    
    for pos in range(32):
        # SIGSEGV handler: 交换 S[i] 和 S[j]
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        
        # SIGFPE handler: XOR 解密
        k = S[(S[i] + S[j]) % 256]
        result.append(encrypted[pos] ^ k)
    
    return bytes(result)

flag = signal_storm_decrypt()
print(f"解密结果: {flag}")

# 如果上面不对，让我重新用标准RC4试试
print("\n使用标准 RC4 (空密钥)...")
S = list(range(256))
# KSA with empty key (all zeros)
j = 0
for i in range(256):
    j = (j + S[i] + 0) % 256  # key[i % keylen] = 0
    S[i], S[j] = S[j], S[i]

# PRGA
i = j = 0
result = []
for byte in encrypted:
    i = (i + 1) % 256
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]
    k = S[(S[i] + S[j]) % 256]
    result.append(byte ^ k)

print(f"标准 RC4 解密: {bytes(result)}")

# 让我再仔细看看初始化代码
# 在 0x1780，使用 SIMD 指令初始化 S 盒为 0,1,2,...,255
# 然后用 KSA 打乱

# 密钥是从 0x4010 读取的21字节
# 但0x4010在.data段，需要看初始值

# 从反汇编看，S盒初始化后立即进行KSA
# KSA中使用的key来自 r8 = 0x4010

# 让我尝试不同的密钥长度
for keylen in [1, 21]:
    S = list(range(256))
    key = [0] * keylen
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % keylen]) % 256
        S[i], S[j] = S[j], S[i]
    
    i = j = 0
    result = []
    for byte in encrypted:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        result.append(byte ^ k)
    
    try:
        decoded = bytes(result).decode('ascii')
        print(f"密钥长度 {keylen}: {decoded}")
    except:
        print(f"密钥长度 {keylen}: {bytes(result)}")
