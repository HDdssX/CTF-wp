#!/usr/bin/env python3
"""分析序列化数据周围的结构"""
import struct

with open('mapdb_v2.bin', 'rb') as f:
    data = f.read()

print('Analyzing data around serialization offset:')
print()

# 检查 0x100240-0x100250 区域
pre_data = data[0x100240:0x100250]
print(f'Pre-serial (0x100240-0x100250): {pre_data.hex()}')

# 解码
decoded = bytes((b ^ 0x80) & 0xff for b in pre_data)
print(f'Decoded: {decoded}')

# 检查 0x100250 开始的序列化数据
serial_data = data[0x100250:0x100300]
print()
print(f'Serialized data (0x100250-0x100300):')
print(f'  {serial_data[:48].hex()}')

# 分析序列化数据大小
# 数组长度在 offset 0x17 (相对于序列化开始)
arr_len_offset = 0x100250 + 0x17
arr_len = struct.unpack('>I', data[arr_len_offset:arr_len_offset+4])[0]
print()
print(f'Array length: {arr_len} bytes')
print(f'Total serialized object size: ~{0x1b + arr_len} bytes')

# 检查序列化数据结束后的内容  
end_offset = 0x100250 + 0x1b + arr_len
print(f'Data after serialized object (0x{end_offset:x}):')
print(f'  {data[end_offset:end_offset+32].hex()}')

# 分析完整的序列化结构
print()
print('=== Serialization Structure ===')
offset = 0x100250
print(f'0x{offset:x}: STREAM_MAGIC={data[offset:offset+2].hex()}')
offset += 2
print(f'0x{offset:x}: STREAM_VERSION={data[offset:offset+2].hex()}')
offset += 2
print(f'0x{offset:x}: TC_ARRAY=0x{data[offset]:02x}')
offset += 1
print(f'0x{offset:x}: TC_CLASSDESC=0x{data[offset]:02x}')
offset += 1
class_name_len = struct.unpack('>H', data[offset:offset+2])[0]
print(f'0x{offset:x}: className len={class_name_len}')
offset += 2
class_name = data[offset:offset+class_name_len]
print(f'0x{offset:x}: className={class_name}')
offset += class_name_len
serial_uid = struct.unpack('>Q', data[offset:offset+8])[0]
print(f'0x{offset:x}: serialVersionUID=0x{serial_uid:016x}')
offset += 8
print(f'0x{offset:x}: flags=0x{data[offset]:02x}')
offset += 1
field_count = struct.unpack('>H', data[offset:offset+2])[0]
print(f'0x{offset:x}: fieldCount={field_count}')
offset += 2
print(f'0x{offset:x}: TC_ENDBLOCKDATA=0x{data[offset]:02x}')
offset += 1
print(f'0x{offset:x}: TC_NULL (superclass)=0x{data[offset]:02x}')
offset += 1
arr_len = struct.unpack('>I', data[offset:offset+4])[0]
print(f'0x{offset:x}: arrayLength={arr_len}')
offset += 4
print(f'0x{offset:x}: [array data starts, {arr_len} bytes]')
print(f'  First 16 bytes: {data[offset:offset+16].hex()}')
