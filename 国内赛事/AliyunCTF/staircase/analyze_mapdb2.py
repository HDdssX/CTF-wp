#!/usr/bin/env python3
"""深入分析 MapDB 文件结构"""
import struct

with open('mapdb_v2.bin', 'rb') as f:
    data = f.read()

print('MapDB File Header Analysis:')
print('='*50)

# 前 8 字节是魔术字节
magic = data[:8]
print(f'Magic: {magic.hex()}')

# 搜索 icon 关键字的位置
print()
print('Searching for "icon" references (encoded):')
# MapDB 使用 XOR 0x80 编码
icon_encoded = bytes((b ^ 0x80) for b in b'icon')
pos = 0
count = 0
while count < 5:
    idx = data.find(icon_encoded, pos)
    if idx == -1:
        break
    context = data[max(0,idx-16):idx+48]
    # 解码上下文
    decoded = bytes((b ^ 0x80) & 0xff for b in context)
    printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in decoded)
    print(f'  0x{idx:06x}: {printable}')
    pos = idx + 1
    count += 1

# 分析序列化数据位置
print()
print('Serialization data location:')
serial_offset = 0x100250
print(f'  Offset: 0x{serial_offset:x}')
print(f'  First 32 bytes: {data[serial_offset:serial_offset+32].hex()}')

# 查找指向这个位置的指针
# MapDB 使用 64-bit 指针
print()
print('Searching for pointers to serialization data...')
target_bytes = struct.pack('<Q', serial_offset)
print(f'  Looking for: {target_bytes.hex()} (little-endian)')
idx = data.find(target_bytes)
if idx != -1:
    print(f'  Found at: 0x{idx:x}')
else:
    print('  Not found (LE)')
    
target_bytes = struct.pack('>Q', serial_offset)
print(f'  Looking for: {target_bytes.hex()} (big-endian)')
idx = data.find(target_bytes)
if idx != -1:
    print(f'  Found at: 0x{idx:x}')
else:
    print('  Not found (BE)')

# 检查文件头中的数据偏移指针
print()
print('File header pointers:')
for i in range(0, 128, 8):
    val = struct.unpack('<Q', data[i:i+8])[0]
    if val > 0 and val < len(data):
        print(f'  Offset 0x{i:02x}: 0x{val:08x} (valid file offset)')
