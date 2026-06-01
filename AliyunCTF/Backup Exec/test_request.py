#!/usr/bin/env python3
"""
测试不同的 Request 格式
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

def create_bind():
    ctx = struct.pack('<HBB', 0, 1, 0)
    ctx += UUID
    ctx += struct.pack('<HH', 1, 0)
    ctx += NDR + struct.pack('<HH', 2, 0)
    
    body = struct.pack('<HH', 0x1000, 0x1000)
    body += struct.pack('<I', 0)
    body += struct.pack('<BBH', 1, 0, 0)
    body += ctx
    
    header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, 0x48, 0, 0)
    return header + body

def test_request(sock, stub, opnum, desc):
    """测试一个 Request"""
    # Request body
    req_body = struct.pack('<IHH', len(stub), 0, opnum)  # alloc_hint, ctx_id, opnum
    req_body += stub
    
    # Pad to 8 bytes
    pad = (8 - len(req_body) % 8) % 8
    req_body += b'\x00' * pad
    
    frag_len = 24 + len(req_body)
    header = struct.pack('<BBBBIHHI', 5, 0, 0, 0x03, 0x10, frag_len, 0, 1)
    request = header + req_body
    
    print(f"\n{desc}")
    print(f"  Request ({len(request)} bytes): {request.hex()[:100]}...")
    
    sock.send(request)
    resp = recv_response(sock, 10)
    
    if resp:
        print(f"  Response ({len(resp)} bytes): {resp.hex()}")
        if len(resp) >= 3:
            ptype = resp[2]
            print(f"  Packet type: {ptype}")
            
            if ptype == 2:  # Response
                print("  [+] Got RPC Response!")
                body = resp[24:]
                print(f"  Body: {body.hex()}")
            elif ptype == 3:  # Fault
                print("  [-] RPC Fault!")
                if len(resp) >= 28:
                    status = struct.unpack('<I', resp[24:28])[0]
                    print(f"  Fault status: 0x{status:08x}")
        return resp
    else:
        print("  No response")
        return None

# 连接并 Bind
print("="*60)
print("Testing Request formats")
print("="*60)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(30)
sock.connect((TARGET, PORT))
print("[+] Connected")

# Bind
sock.send(create_bind())
resp = recv_response(sock)
if resp[2] != 12:
    print("[-] Bind failed")
    exit(1)
print("[+] Bind successful")

# 测试空 stub
test_request(sock, b'', 0, "Empty stub, opnum=0")

# 重新连接
sock.close()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(30)
sock.connect((TARGET, PORT))
sock.send(create_bind())
recv_response(sock)

# 测试简单的 4 字节 stub
test_request(sock, struct.pack('<I', 0), 0, "4 bytes (0), opnum=0")

# 重新连接测试不同 opnum
for opnum in range(5):
    sock.close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((TARGET, PORT))
    sock.send(create_bind())
    recv_response(sock)
    
    test_request(sock, struct.pack('<I', 0), opnum, f"4 bytes (0), opnum={opnum}")

# 测试带文件路径的不同格式
filepath = "C:\\flag.txt"  # 简化的路径

# 格式 1: 简单的宽字符串
sock.close()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(30)
sock.connect((TARGET, PORT))
sock.send(create_bind())
recv_response(sock)

stub1 = filepath.encode('utf-16-le') + b'\x00\x00'
test_request(sock, stub1, 0, "Simple UTF-16LE string")

# 格式 2: NDR conformant string
sock.close()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(30)
sock.connect((TARGET, PORT))
sock.send(create_bind())
recv_response(sock)

n = len(filepath) + 1
stub2 = struct.pack('<III', n, 0, n) + filepath.encode('utf-16-le') + b'\x00\x00'
test_request(sock, stub2, 0, "NDR conformant string")

# 格式 3: 带指针的 NDR string
sock.close()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(30)
sock.connect((TARGET, PORT))
sock.send(create_bind())
recv_response(sock)

# NDR unique pointer + conformant string
stub3 = struct.pack('<I', 0x00020000)  # unique pointer referent id
stub3 += struct.pack('<III', n, 0, n) + filepath.encode('utf-16-le') + b'\x00\x00'
test_request(sock, stub3, 0, "NDR unique pointer + string")

# 测试更长的等待时间
print("\n" + "="*60)
print("Testing with longer wait")
print("="*60)

sock.close()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(60)
sock.connect((TARGET, PORT))
sock.send(create_bind())
recv_response(sock)

stub = struct.pack('<III', n, 0, n) + filepath.encode('utf-16-le') + b'\x00\x00'
req_body = struct.pack('<IHH', len(stub), 0, 0)
req_body += stub
pad = (8 - len(req_body) % 8) % 8
req_body += b'\x00' * pad

frag_len = 24 + len(req_body)
header = struct.pack('<BBBBIHHI', 5, 0, 0, 0x03, 0x10, frag_len, 0, 1)
request = header + req_body

print(f"Sending Request ({len(request)} bytes)...")
sock.send(request)

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
                print(f"  Received {len(chunk)} bytes at {time.time()-start:.1f}s")
                
                # 检查是否完整
                if len(response) >= 10:
                    frag_len = struct.unpack('<H', response[8:10])[0]
                    if len(response) >= frag_len:
                        break
            else:
                print("  Connection closed")
                break
        except socket.timeout:
            continue
    
    print(f"Total: {len(response)} bytes")
    if response:
        print(f"  {response.hex()}")
except Exception as e:
    print(f"Error: {e}")

sock.close()
print("\nDone")
