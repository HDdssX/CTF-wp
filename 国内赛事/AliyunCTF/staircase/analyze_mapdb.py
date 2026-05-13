#!/usr/bin/env python3
"""分析 MapDB 元数据结构"""

with open('F:/CTF/CTF-wp/AliyunCTF/staircase/mapdb_v2.bin', 'rb') as f:
    data = f.read()

# 尝试 XOR 0x80 解码 0x100080 区域
region = data[0x100080:0x100250]
decoded = bytes((b ^ 0x80) & 0xff for b in region)

print('Decoded metadata (0x100080-0x100250):')
# 分段打印
pos = 0
while pos < len(decoded):
    # 找到下一个 null 或不可打印字符
    end = pos
    while end < len(decoded) and 32 <= decoded[end] < 127:
        end += 1
    if end > pos:
        s = decoded[pos:end].decode('ascii', errors='replace')
        print(f'  0x{0x100080+pos:06x}: "{s}"')
    pos = end + 1
