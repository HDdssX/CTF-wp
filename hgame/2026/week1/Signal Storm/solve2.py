#!/usr/bin/env python3
# Signal Storm - 完整逆向分析
# 这道题使用 sigsetjmp/siglongjmp 和信号处理来实现 RC4 变种加密

# 加密后的数据
encrypted = bytes([
    0xe3, 0x36, 0xd9, 0xc8, 0xc9, 0xc1, 0x60, 0x82,
    0x75, 0xd9, 0x11, 0x25, 0xd5, 0xb2, 0x4b, 0x1c,
    0x4d, 0xe6, 0x6d, 0x71, 0x1c, 0xaf, 0x1c, 0xf1,
    0x06, 0xa5, 0x1c, 0x26, 0x7f, 0xf6, 0x5a, 0x1a
])

# 分析程序流程:
# 1. main (0x1300) 设置三个信号处理器:
#    - SIGSEGV (11): handler at 0x1640 - S盒交换
#    - SIGFPE (8):   handler at 0x16e0 - XOR解密  
#    - SIGTRAP (5):  handler at 0x1740 - 旋转密钥
#
# 2. 调用 init_rc4 (0x1780) 初始化 S 盒和密钥调度
#
# 3. 主循环 32 次:
#    - sigsetjmp 保存状态
#    - 触发 SIGSEGV (通过写入地址0)
#    - sigsetjmp 
#    - 触发 SIGFPE (通过除零)
#    - sigsetjmp
#    - 触发 SIGTRAP (可能通过某种方式)
#    - 计数器++

# 让我模拟完整的加密流程

# S 盒 (256 bytes) - 初始化为 0..255
S = list(range(256))

# 密钥缓冲区 (21 bytes) - 从 0x4010，初始为全0
key = [0] * 21

# 状态变量
idx = 0   # 对应 0x4068
j = 0     # 对应 0x4064

# 输入缓冲区 - 用户输入会存储在 0x4080
# 程序会把加密后的用户输入与 encrypted 比较

# init_rc4 (0x1780) 的模拟:
# 1. 初始化 S[i] = i for i in 0..255
# 2. KSA: 打乱 S 盒

print("=== 模拟 RC4 初始化 (0x1780) ===")

# 重新初始化
S = list(range(256))
j = 0

# KSA with key (21 bytes of 0)
for i in range(256):
    # 从代码 0x1850-0x18ad 分析:
    # j = (j + S[i] + key[i % 21]) % 256
    j = (j + S[i] + key[i % 21]) % 256
    S[i], S[j] = S[j], S[i]

print(f"S盒前16字节: {S[:16]}")

# 现在模拟信号处理的加密过程
# 重置索引
idx = 0
j = 0

print("\n=== 模拟信号处理加密流程 ===")

# 主循环 32 次
result = []

for pos in range(32):
    # SIGSEGV handler (0x1640):
    # idx = (idx + 1) % 256
    # j = (j + S[idx]) % 256  
    # swap(S[idx], S[j])
    
    idx = (idx + 1) % 256
    tmp = S[idx]
    j = (j + tmp + key[idx % 21]) % 256  # 从 0x1671-0x1694 分析
    S[idx], S[j] = S[j], S[idx]
    
    # SIGFPE handler (0x16e0):
    # if pos <= 99:
    #   k = S[(S[idx] + S[j]) % 256]
    #   input[pos] ^= k
    
    k = S[(S[idx] + S[j]) % 256]
    result.append(encrypted[pos] ^ k)

decrypted = bytes(result)
print(f"解密结果: {decrypted}")

# 如果上面不对，可能是 KSA 阶段的 key 不是全0
# 让我试试只做 PRGA，不带 key 的 KSA

print("\n=== 尝试标准 RC4 PRGA ===")

S = list(range(256))
# 不做 KSA，直接 PRGA

i = j = 0
result = []

for byte in encrypted:
    i = (i + 1) % 256
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]
    k = S[(S[i] + S[j]) % 256]
    result.append(byte ^ k)

print(f"无KSA PRGA: {bytes(result)}")

# 再仔细看 SIGSEGV handler (0x1640)
# 它修改了 S 盒的交换逻辑

print("\n=== 分析 SIGSEGV handler ===")
# 0x1651: mov eax, [0x4068]    ; idx
# 0x1657: add eax, 1
# 0x165b-0x1663: eax = (eax + 1) % 256
# 0x166b: mov [0x4068], eax    ; idx = (idx+1) % 256
# 0x167c: movzbl edx, [rsi+rdi] ; tmp = S[idx]
# 0x1683: add edx, [0x4064]     ; tmp += j
# 0x1689-0x1698: 计算 idx % 21
# 0x16a3: movzbl eax, [rcx+rax] ; key[idx % 21]  
# 0x16a7-0x16b4: j = (tmp + key[idx%21]) % 256
# 0x16c0: mov [rsi+rdi], dl     ; S[idx] = S[j]
# 0x16ca: mov [rsi+rax], r8b    ; S[j] = tmp

print("\n=== 重新分析完整流程 ===")

# S 盒初始化
S = list(range(256))
key = [0] * 21  # 密钥是 21 字节的 0

# KSA (从 0x1850-0x18ad)
j = 0
for i in range(256):
    j = (j + S[i] + key[i % 21]) % 256
    S[i], S[j] = S[j], S[i]

print(f"KSA 后 S 盒: {S[:16]}")

# 重置状态
idx = 0  
j = 0

# 加密/解密 32 字节
result = []
for byte in encrypted:
    # SIGSEGV: S盒交换
    idx = (idx + 1) % 256
    tmp = S[idx]
    # 关键: j 的更新包含 key
    j = (j + tmp + key[idx % 21]) % 256
    S[idx], S[j] = S[j], S[idx]
    
    # SIGFPE: XOR
    k = S[(S[idx] + S[j]) % 256]
    result.append(byte ^ k)

print(f"解密: {bytes(result)}")

# 既然 key 全为 0，实际上等同于标准 RC4
# 让我核实一下

print("\n=== 验证：标准 RC4 ===")

S = list(range(256))
j = 0
for i in range(256):
    j = (j + S[i]) % 256  # key=0 所以 +key[i%21] 无效
    S[i], S[j] = S[j], S[i]

i = j = 0
result = []
for byte in encrypted:
    i = (i + 1) % 256
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]
    k = S[(S[i] + S[j]) % 256]
    result.append(byte ^ k)

print(f"标准 RC4 解密: {bytes(result)}")

# 问题可能在于程序中 KSA 和 PRGA 之间的状态没有重置
# 或者有额外的变换

print("\n=== 尝试不重置状态 ===")

S = list(range(256))
j = 0
# KSA
for i in range(256):
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]

# PRGA - 不重置 j
# i 从 0 开始，但 j 保持 KSA 结束时的值
i = 0
result = []
for byte in encrypted:
    i = (i + 1) % 256
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]
    k = S[(S[i] + S[j]) % 256]
    result.append(byte ^ k)

print(f"不重置j: {bytes(result)}")

# 尝试分析 SIGTRAP handler (0x1740)
# 它做了一个旋转操作 (memmove)
print("\n=== 分析 SIGTRAP handler (密钥旋转) ===")
# memmove(key, key+1, 20)  ; 左移1字节
# key[20] = key[0]         ; 原来的第一个字节放到末尾

# 这意味着每轮循环后密钥会旋转
# 但初始密钥全为0，旋转后仍为0

# 让我检查一下程序是否有初始化 key 的地方
# 在 0x1220 有一个函数读取 /proc/self/status
# 如果检测到调试器 (TracerPid != 0)，会 XOR 修改某些数据

# 实际运行时 TracerPid = 0，所以 XOR 0 不改变任何东西

print("\n=== 最终答案 ===")
# 由于所有分析都指向标准 RC4 with key = 0
# 但解密结果不是可读文本，可能我遗漏了什么

# 让我尝试逆序处理
S = list(range(256))
# 不做 KSA

i = j = 0
result = []
for byte in encrypted:
    i = (i + 1) % 256
    j = (j + S[i]) % 256
    S[i], S[j] = S[j], S[i]
    k = S[(S[i] + S[j]) % 256]
    result.append(byte ^ k)

print(f"无KSA: {bytes(result)}")

# 尝试密钥为其他值
print("\n=== 尝试不同密钥 ===")

# 从 rodata 看，0x20c0 处有 0x15 (21)
# 这可能暗示密钥长度

# 尝试密钥为 hgame{
test_keys = [
    b"hgame{",
    b"\x00" * 21,
    bytes(range(21)),
]

for tk in test_keys:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + tk[i % len(tk)]) % 256
        S[i], S[j] = S[j], S[i]
    
    i = j = 0
    result = []
    for byte in encrypted:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        result.append(byte ^ k)
    
    print(f"key={tk[:6]}...: {bytes(result)[:20]}...")
