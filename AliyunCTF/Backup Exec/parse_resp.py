#!/usr/bin/env python3
import struct

# Bind ACK 响应
resp = bytes.fromhex('05000c03100000003c000000000000000010001043b1000006003632383331000100000000000000045d888aeb1cc9119fe808002b10486002000000')

print('Parsing Bind ACK response:')
print(f'  Version: {resp[0]}.{resp[1]}')
print(f'  Packet type: {resp[2]} (12=BIND_ACK)')
print(f'  Flags: 0x{resp[3]:02x}')
print(f'  Data rep: 0x{struct.unpack("<I", resp[4:8])[0]:08x}')
print(f'  Frag length: {struct.unpack("<H", resp[8:10])[0]}')
print(f'  Auth length: {struct.unpack("<H", resp[10:12])[0]}')
print(f'  Call ID: {struct.unpack("<I", resp[12:16])[0]}')

# Bind ACK body
print(f'\n  Max xmit frag: {struct.unpack("<H", resp[16:18])[0]}')
print(f'  Max recv frag: {struct.unpack("<H", resp[18:20])[0]}')
print(f'  Assoc group: 0x{struct.unpack("<I", resp[20:24])[0]:08x}')

# Secondary address
sec_addr_len = struct.unpack('<H', resp[24:26])[0]
print(f'  Secondary addr length: {sec_addr_len}')
sec_addr = resp[26:26+sec_addr_len]
print(f'  Secondary addr: {sec_addr}')

# Context results
offset = 26 + sec_addr_len
# Pad to 4-byte boundary
offset = (offset + 3) & ~3
print(f'\n  Context results at offset {offset}:')
n_results = struct.unpack('<B', resp[offset:offset+1])[0]
print(f'  Num results: {n_results}')

offset += 4  # n_results + reserved
for i in range(n_results):
    result = struct.unpack('<H', resp[offset:offset+2])[0]
    reason = struct.unpack('<H', resp[offset+2:offset+4])[0]
    print(f'    Result {i}: {result} (0=acceptance), reason: {reason}')
    
    transfer_syntax = resp[offset+4:offset+20]
    print(f'    Transfer syntax: {transfer_syntax.hex()}')
    offset += 24
