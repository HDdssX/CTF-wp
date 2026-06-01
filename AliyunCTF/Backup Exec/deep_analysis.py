#!/usr/bin/env python3
"""
深入分析服务器响应条件
"""

import socket
import struct
import time

TARGET = "116.62.114.4"
PORT = 62831

UUID = bytes.fromhex('8902e062bd447b49b85fbc340fbcc2b0')
NDR = bytes.fromhex('045d888aeb1cc9119fe808002b104860')

def recv_response(sock, timeout=10):
    sock.settimeout(timeout)
    data = b""
    
    try:
        while len(data) < 24:
            chunk = sock.recv(24 - len(data))
            if not chunk:
                break
            data += chunk
        
        if len(data) >= 10:
            frag_length = struct.unpack('<H', data[8:10])[0]
            while len(data) < frag_length:
                chunk = sock.recv(frag_length - len(data))
                if not chunk:
                    break
                data += chunk
    except socket.timeout:
        pass
    
    return data

def test_bind(frag_len, desc):
    """测试特定 frag_length 的 Bind"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    try:
        sock.connect((TARGET, PORT))
        
        ctx = struct.pack('<HBB', 0, 1, 0)
        ctx += UUID
        ctx += struct.pack('<HH', 1, 0)
        ctx += NDR + struct.pack('<HH', 2, 0)
        
        body = struct.pack('<HH', 0x1000, 0x1000)
        body += struct.pack('<I', 0)
        body += struct.pack('<BBH', 1, 0, 0)
        body += ctx
        
        header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, frag_len, 0, 0)
        pdu = header + body
        
        sock.send(pdu)
        resp = recv_response(sock, 5)
        
        result = "RESPONSE" if resp else "NO RESPONSE"
        print(f"  frag_len=0x{frag_len:04X} ({frag_len}): {result}")
        if resp:
            print(f"    {resp.hex()[:80]}")
        
        sock.close()
        return resp
        
    except Exception as e:
        print(f"  frag_len=0x{frag_len:04X}: ERROR - {e}")
        sock.close()
        return None

print("="*60)
print("Testing frag_length values")
print("="*60)

# 已知 0x48 可以工作，测试附近的值
for frag_len in [0x40, 0x44, 0x48, 0x4C, 0x50, 0x60, 0x70, 0x80]:
    test_bind(frag_len, f"frag_len={frag_len}")
    time.sleep(0.3)

# 测试 Request 的 frag_length
print("\n" + "="*60)
print("Testing Request frag_length after successful Bind")
print("="*60)

for req_frag_len in [0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    
    # Successful Bind
    ctx = struct.pack('<HBB', 0, 1, 0)
    ctx += UUID
    ctx += struct.pack('<HH', 1, 0)
    ctx += NDR + struct.pack('<HH', 2, 0)
    
    body = struct.pack('<HH', 0x1000, 0x1000)
    body += struct.pack('<I', 0)
    body += struct.pack('<BBH', 1, 0, 0)
    body += ctx
    
    header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, 0x48, 0, 0)
    sock.send(header + body)
    resp = recv_response(sock, 5)
    
    if resp and resp[2] == 12:
        # Send Request with specific frag_length
        stub = b'\x00' * 4
        req_body = struct.pack('<IHH', 4, 0, 0) + stub
        
        header = struct.pack('<BBBBIHHI', 5, 0, 0, 0x03, 0x10, req_frag_len, 0, 1)
        request = header + req_body
        
        # Pad to match frag_len
        if len(request) < req_frag_len:
            request += b'\x00' * (req_frag_len - len(request))
        
        sock.send(request)
        resp = recv_response(sock, 5)
        
        result = "RESPONSE" if resp else "NO RESPONSE"
        print(f"  req_frag_len=0x{req_frag_len:04X}: {result}")
        if resp:
            print(f"    Packet type: {resp[2]}")
            print(f"    {resp.hex()[:80]}")
    
    sock.close()
    time.sleep(0.3)

# 测试不同的 packet type
print("\n" + "="*60)
print("Testing different packet types")
print("="*60)

for ptype in [0, 1, 2, 11, 12, 14, 16]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    
    ctx = struct.pack('<HBB', 0, 1, 0)
    ctx += UUID
    ctx += struct.pack('<HH', 1, 0)
    ctx += NDR + struct.pack('<HH', 2, 0)
    
    body = struct.pack('<HH', 0x1000, 0x1000)
    body += struct.pack('<I', 0)
    body += struct.pack('<BBH', 1, 0, 0)
    body += ctx
    
    header = struct.pack('<BBBBIHHI', 5, 0, ptype, 0x03, 0x10, 0x48, 0, 0)
    pdu = header + body
    
    sock.send(pdu)
    resp = recv_response(sock, 5)
    
    ptype_names = {0: 'REQUEST', 1: 'PING', 2: 'RESPONSE', 11: 'BIND', 12: 'BIND_ACK', 14: 'ALTER_CTX', 16: 'AUTH3'}
    name = ptype_names.get(ptype, 'UNKNOWN')
    result = "RESPONSE" if resp else "NO RESPONSE"
    print(f"  ptype={ptype} ({name}): {result}")
    if resp:
        print(f"    {resp.hex()[:80]}")
    
    sock.close()
    time.sleep(0.3)

# 在 Bind 之后立即发送第二个数据包
print("\n" + "="*60)
print("Testing immediate second packet after Bind")
print("="*60)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
sock.connect((TARGET, PORT))

# Bind
ctx = struct.pack('<HBB', 0, 1, 0)
ctx += UUID
ctx += struct.pack('<HH', 1, 0)
ctx += NDR + struct.pack('<HH', 2, 0)

body = struct.pack('<HH', 0x1000, 0x1000)
body += struct.pack('<I', 0)
body += struct.pack('<BBH', 1, 0, 0)
body += ctx

header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, 0x48, 0, 0)
bind_pdu = header + body

# Request with frag_len=0x48
stub = b'\x00' * 16
req_body = struct.pack('<IHH', 16, 0, 0) + stub

# Pad to 0x48
req_header = struct.pack('<BBBBIHHI', 5, 0, 0, 0x03, 0x10, 0x48, 0, 1)
request = req_header + req_body
if len(request) < 0x48:
    request += b'\x00' * (0x48 - len(request))

# 发送两个包在一起
combined = bind_pdu + request
print(f"Sending Bind + Request together ({len(combined)} bytes)")
sock.send(combined)

# 接收所有响应
sock.settimeout(10)
all_resp = b""
try:
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        all_resp += chunk
        print(f"  Received {len(chunk)} bytes")
except socket.timeout:
    pass

print(f"Total response: {len(all_resp)} bytes")
if all_resp:
    print(f"  {all_resp.hex()}")
    
    # 解析多个响应
    offset = 0
    pkt_num = 0
    while offset < len(all_resp):
        if offset + 10 > len(all_resp):
            break
        frag_len = struct.unpack('<H', all_resp[offset+8:offset+10])[0]
        pkt = all_resp[offset:offset+frag_len]
        print(f"  Packet {pkt_num}: type={pkt[2]}, len={frag_len}")
        print(f"    {pkt.hex()}")
        offset += frag_len
        pkt_num += 1

sock.close()

print("\nDone")
