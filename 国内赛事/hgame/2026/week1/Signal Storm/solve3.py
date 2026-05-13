#!/usr/bin/env python3
"""
Signal Storm - CTF 逆向分析
关键点：
1. 程序使用 sigsetjmp/siglongjmp 配合信号处理实现控制流
2. 三个信号处理器配合 RC4 变种加密
3. 信号触发顺序：SIGSEGV -> SIGFPE -> SIGTRAP（循环32次）
"""

# 目标加密数据 (0x20a0)
encrypted = bytes([
    0xe3, 0x36, 0xd9, 0xc8, 0xc9, 0xc1, 0x60, 0x82,
    0x75, 0xd9, 0x11, 0x25, 0xd5, 0xb2, 0x4b, 0x1c,
    0x4d, 0xe6, 0x6d, 0x71, 0x1c, 0xaf, 0x1c, 0xf1,
    0x06, 0xa5, 0x1c, 0x26, 0x7f, 0xf6, 0x5a, 0x1a
])

# 全局状态
class State:
    def __init__(self):
        # S-box at 0x4100 (256 bytes)
        self.S = list(range(256))
        # Key buffer at 0x4010 (21 bytes) 
        self.key = [0] * 21
        # idx at 0x4068
        self.idx = 0
        # j at 0x4064
        self.j = 0
        # counter at 0x4060
        self.counter = 0
        # Input buffer at 0x4080 (32 bytes)
        self.input = bytearray(32)

def init_sbox(state):
    """模拟 0x1780 - 初始化 S-box"""
    state.S = list(range(256))
    
    # KSA (Key Scheduling Algorithm)
    state.j = 0
    for i in range(256):
        state.j = (state.j + state.S[i] + state.key[i % 21]) % 256
        state.S[i], state.S[state.j] = state.S[state.j], state.S[i]

def sigsegv_handler(state):
    """模拟 SIGSEGV handler (0x1640) - S-box 交换"""
    # idx = (idx + 1) % 256
    state.idx = (state.idx + 1) % 256
    
    # 获取 S[idx]
    tmp = state.S[state.idx]
    
    # j = (j + S[idx] + key[idx % 21]) % 256
    state.j = (state.j + tmp + state.key[state.idx % 21]) % 256
    
    # 交换 S[idx] 和 S[j]
    state.S[state.idx], state.S[state.j] = state.S[state.j], state.S[state.idx]

def sigfpe_handler(state):
    """模拟 SIGFPE handler (0x16e0) - XOR 加密"""
    # 只处理前 100 个字节 (cmp $0x63)
    if state.counter > 99:
        return
    
    # k = S[(S[idx] + S[j]) % 256]
    k = state.S[(state.S[state.idx] + state.S[state.j]) % 256]
    
    # input[counter] ^= k
    state.input[state.counter] ^= k

def sigtrap_handler(state):
    """模拟 SIGTRAP handler (0x1740) - 密钥旋转"""
    # memmove(key, key+1, 20) - 左移
    first = state.key[0]
    for i in range(20):
        state.key[i] = state.key[i + 1]
    # key[20] = first_byte
    state.key[20] = first

def decrypt():
    state = State()
    
    # 复制加密数据到输入缓冲区
    state.input = bytearray(encrypted)
    
    # 初始化 S-box
    init_sbox(state)
    
    # 重置状态用于 PRGA
    state.idx = 0
    state.j = 0
    state.counter = 0
    
    # 主循环 32 次
    for _ in range(32):
        # 每轮触发三个信号
        sigsegv_handler(state)  # S-box 交换
        sigfpe_handler(state)   # XOR
        sigtrap_handler(state)  # 密钥旋转
        state.counter += 1
    
    return bytes(state.input)

print("=== 完整模拟 ===")
result = decrypt()
print(f"解密结果: {result}")

# 分析发现：密钥旋转对全0密钥无效
# 让我检查是否有遗漏

print("\n=== 分析信号触发顺序 ===")
# 从 main 函数分析:
# 0x143b: mov eax, 0; mov [0], eax -> 触发 SIGSEGV
# 0x1497: idiv ecx (ecx=0) -> 触发 SIGFPE  
# 0x150d: raise(5) -> 触发 SIGTRAP

# 关键：循环 32 次 (cmp $0x1f)

# 再次确认流程
print("\n=== 标准 RC4 对比 ===")

# 由于 key 全为 0，旋转不改变 key
# 所以这就是标准 RC4

import struct

# 从程序比较逻辑分析 (0x14b5-0x153c)
# 加密后的数据与两组常量比较：
# 第一组: 0x8260c1c9c8d936e3, 0x1c4bb2d52511d975
# 第二组: 0xf11caf1c716de64d, 0x1a5af67f261ca506

# 这些是加密后应该等于的值（实际就是 encrypted 数据）
check1 = struct.pack('<QQ', 0x8260c1c9c8d936e3, 0x1c4bb2d52511d975)
check2 = struct.pack('<QQ', 0xf11caf1c716de64d, 0x1a5af67f261ca506)

print(f"Check1: {check1.hex()}")
print(f"Check2: {check2.hex()}")
print(f"Encrypted: {encrypted[:16].hex()}")
print(f"Match: {check1 == encrypted[:16]}")

# 确认加密数据正确

# 现在关键问题：密钥是什么？
# 程序开头有个反调试检查读取 TracerPid
# 正常运行时 TracerPid = 0
# 但关键是这个值会 XOR 到 0x4010 的数据

# 查看 0x1220 函数：
# 它读取 /proc/self/status，解析 TracerPid
# 然后用这个值 XOR 地址 0x4010 开始的 21 字节

# 正常情况下 TracerPid = 0，所以 XOR 0 不改变数据

print("\n=== 分析初始密钥 ===")
# 地址 0x4010 在 .data 段
# 初始值应该从二进制文件读取

# 让我重新检查 .data 段
# 从 ELF 头分析:
# .data 在文件偏移约 0x2d40，虚拟地址 0x3d40
# 0x4010 - 0x3d40 = 0x2d0，所以文件偏移 = 0x2d40 + 0x2d0 = 0x3010

# 但实际上看反汇编:
# 0x12ad: lea rdx, 0x4010  - 这是 .bss 或 .data 中的地址

print("\n=== 最终尝试 - 手动穷举简单密钥 ===")

def rc4_decrypt(key_bytes, data):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key_bytes[i % len(key_bytes)]) % 256
        S[i], S[j] = S[j], S[i]
    
    i = j = 0
    result = []
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        result.append(byte ^ k)
    return bytes(result)

# 尝试一些可能的密钥
test_keys = [
    b'\x00' * 21,
    b'signal_storm',
    b'hgame',
    b'hgame2026',
    b'ctf',
]

for key in test_keys:
    result = rc4_decrypt(key, encrypted)
    print(f"Key '{key.decode('latin1')[:10]}...': {result[:16]}...")

# 或者密钥可能就是一个简单的字节
print("\n=== 单字节密钥穷举 ===")
for k in range(256):
    result = rc4_decrypt(bytes([k]), encrypted)
    if result.startswith(b'hgame{') or result.startswith(b'flag{'):
        print(f"Found! Key={k}: {result}")
        break
    # 检查是否全部可打印
    if all(32 <= b <= 126 for b in result):
        print(f"Printable result with key={k}: {result}")
