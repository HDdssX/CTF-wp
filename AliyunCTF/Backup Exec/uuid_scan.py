#!/usr/bin/env python3
"""
探测所有可能的 UUID
"""

import socket
import struct

TARGET = "116.62.114.4"
PORT = 62831

def make_bind_pdu(interface_uuid):
    transfer_syntax = b'\x04\x5d\x88\x8a\xeb\x1c\xc9\x11\x9f\xe8\x08\x00\x2b\x10\x48\x60'
    transfer_version = struct.pack('<HH', 2, 0)
    
    ctx_item = struct.pack('<HBB', 0, 1, 0)
    ctx_item += interface_uuid
    ctx_item += struct.pack('<HH', 1, 0)
    ctx_item += transfer_syntax + transfer_version
    
    bind_body = struct.pack('<HH', 4096, 4096)
    bind_body += struct.pack('<I', 0)
    bind_body += struct.pack('<BBH', 1, 0, 0)
    bind_body += ctx_item
    
    frag_len = 24 + len(bind_body)
    header = struct.pack(
        '<BBBBIHHI',
        5, 0, 11, 0x03,
        0x10, frag_len, 0, 0
    )
    
    return header + bind_body

def try_uuid(uuid_bytes, description=""):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((TARGET, PORT))
        
        bind_pdu = make_bind_pdu(uuid_bytes)
        sock.send(bind_pdu)
        
        sock.settimeout(3)
        resp = sock.recv(1024)
        sock.close()
        
        if resp and len(resp) >= 3:
            ptype = resp[2]
            if ptype == 12:  # BIND_ACK
                print(f"[+] SUCCESS: {uuid_bytes.hex()} - {description}")
                print(f"    Response: {resp.hex()}")
                return True
            else:
                print(f"[-] {uuid_bytes.hex()} - rejected (ptype={ptype})")
        return False
    except Exception as e:
        print(f"[-] {uuid_bytes.hex()} - error: {e}")
        return False

# 已知的 Backup Exec 相关 UUID
# 从之前的响应中，我们得到了一个成功的绑定
# 响应包含 "62831" 字符串，这是端口号

# UUID 格式: {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}
# 存储为 little-endian 

uuids_to_try = [
    # 标准格式的 UUID
    (bytes.fromhex('44c7787d8d4f1b4f8a864962c36ae41e'), "7d78c744-4f8d-4f1b-8a86-4962c36ae41e"),
    (bytes.fromhex('44c7787d8d4f1b4f8a864962c36ae41f'), "7d78c744-4f8d-4f1b-8a86-4962c36ae41f"),
    
    # Little-endian UUID 格式转换
    # {7d78c744-4f8d-4f1b-8a86-4962c36ae41e} -> 44c7787d-8d4f-1b4f-8a86-4962c36ae41e (LE)
    (struct.pack('<IHH', 0x7d78c744, 0x4f8d, 0x4f1b) + bytes.fromhex('8a864962c36ae41e'), "7d78c744 (LE format 1)"),
    (struct.pack('<IHH', 0x7d78c744, 0x4f8d, 0x4f1b) + bytes.fromhex('8a864962c36ae41f'), "7d78c744 (LE format 2)"),
    
    # Null UUID
    (b'\x00' * 16, "Null UUID"),
    
    # 尝试其他常见 Backup Exec UUID
    (bytes.fromhex('00000000000000000000000000000001'), "UUID 1"),
]

print(f"[*] Testing UUIDs against {TARGET}:{PORT}")
print("="*60)

for uuid_bytes, desc in uuids_to_try:
    try_uuid(uuid_bytes, desc)
