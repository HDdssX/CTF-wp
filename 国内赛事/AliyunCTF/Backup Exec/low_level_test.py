#!/usr/bin/env python3
"""
低级协议测试 - 发送不同的二进制数据包
"""

import socket
import struct
import time

TARGET = "116.62.114.4"
PORT = 62831

def send_and_recv(data, desc, timeout=10):
    """发送数据并接收响应"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((TARGET, PORT))
        
        print(f"\n{desc}")
        print(f"  Send ({len(data)} bytes): {data.hex()[:80]}...")
        
        sock.send(data)
        
        # 等待响应
        sock.settimeout(5)
        response = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                # 检查是否收到完整数据
                if len(response) >= 10:
                    try:
                        frag_len = struct.unpack('<H', response[8:10])[0]
                        if len(response) >= frag_len:
                            break
                    except:
                        pass
        except socket.timeout:
            pass
        
        sock.close()
        
        if response:
            print(f"  Recv ({len(response)} bytes): {response.hex()}")
            return response
        else:
            print("  No response")
            return None
            
    except Exception as e:
        print(f"  Error: {e}")
        return None

# UUID 变体测试
UUID1 = bytes.fromhex('8902e062bd447b49b85fbc340fbcc2b0')  # 从二进制直接提取
UUID2 = bytes.fromhex('62e00289-44bd-497b-b85f-bc340fbcc2b0'.replace('-', ''))  # 标准格式
UUID3 = bytes.fromhex('62e0028944bd497bb85fbc340fbcc2b0')  # 移除连字符

# 测试不同的 RPC 版本
print("="*60)
print("Testing different RPC formats")
print("="*60)

# 测试 1: RPC version 5.0
ndr = bytes.fromhex('045d888aeb1cc9119fe808002b104860')

for uuid in [UUID1]:
    ctx = struct.pack('<HBB', 0, 1, 0)  # ctx_id, n_transfer_syn, reserved
    ctx += uuid
    ctx += struct.pack('<HH', 1, 0)  # if_version major, minor
    ctx += ndr + struct.pack('<HH', 2, 0)  # transfer syntax version
    
    body = struct.pack('<HH', 0x1000, 0x1000)  # max_xmit, max_recv
    body += struct.pack('<I', 0)  # assoc_group
    body += struct.pack('<BBH', 1, 0, 0)  # n_context_elem, reserved
    body += ctx
    
    frag_len = 24 + len(body)
    
    # 不同的 flags 组合
    for flags in [0x03, 0x01, 0x02, 0x00, 0x20, 0x23]:
        header = struct.pack('<BBBBIHHI', 5, 0, 11, flags, 0x10, frag_len, 0, 0)
        pdu = header + body
        send_and_recv(pdu, f"RPC 5.0 Bind flags=0x{flags:02x} UUID={uuid.hex()[:8]}...")

# 测试 2: 更短的数据包
print("\n" + "="*60)
print("Testing minimal packets")
print("="*60)

# 最小化 bind
min_bind = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, 24, 0, 0)
send_and_recv(min_bind, "Minimal RPC header only")

# 测试 3: 不同的数据表示
print("\n" + "="*60)
print("Testing different data representations")
print("="*60)

for data_rep in [0x10, 0x00, 0x20, 0x10000000]:
    header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, data_rep & 0xFFFFFFFF, 72, 0, 0)
    
    ctx = struct.pack('<HBB', 0, 1, 0)
    ctx += UUID1
    ctx += struct.pack('<HH', 1, 0)
    ctx += ndr + struct.pack('<HH', 2, 0)
    
    body = struct.pack('<HH', 0x1000, 0x1000)
    body += struct.pack('<I', 0)
    body += struct.pack('<BBH', 1, 0, 0)
    body += ctx
    
    pdu = header + body
    send_and_recv(pdu, f"RPC data_rep=0x{data_rep:08x}")

# 测试 4: 长时间等待
print("\n" + "="*60)
print("Testing with longer timeout")
print("="*60)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(30)
try:
    sock.connect((TARGET, PORT))
    print("Connected, waiting 10 seconds for server to send data first...")
    
    sock.settimeout(10)
    try:
        data = sock.recv(4096)
        print(f"Server sent: {data.hex() if data else 'Nothing'}")
    except socket.timeout:
        print("No data from server")
    
    # 现在发送 bind
    ctx = struct.pack('<HBB', 0, 1, 0)
    ctx += UUID1
    ctx += struct.pack('<HH', 1, 0)
    ctx += ndr + struct.pack('<HH', 2, 0)
    
    body = struct.pack('<HH', 0x1000, 0x1000)
    body += struct.pack('<I', 0)
    body += struct.pack('<BBH', 1, 0, 0)
    body += ctx
    
    frag_len = 24 + len(body)
    header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, frag_len, 0, 0)
    pdu = header + body
    
    print(f"Sending Bind ({len(pdu)} bytes)...")
    sock.send(pdu)
    
    # 等待更长时间
    print("Waiting for response (30 seconds)...")
    sock.settimeout(30)
    try:
        response = b""
        start = time.time()
        while time.time() - start < 30:
            try:
                chunk = sock.recv(4096)
                if chunk:
                    response += chunk
                    print(f"  Received {len(chunk)} bytes")
                else:
                    break
            except socket.timeout:
                continue
        
        print(f"Total response: {len(response)} bytes")
        if response:
            print(f"  Hex: {response.hex()}")
    except Exception as e:
        print(f"Error: {e}")
        
    sock.close()
except Exception as e:
    print(f"Error: {e}")

print("\nDone")
