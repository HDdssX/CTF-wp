#!/usr/bin/env python3
"""
分析之前成功的 bind 响应
"""

# 之前成功的响应数据：
# 05000c03100000003c000000000000000010001029a600000600363238333100010000000200010000000000000000000000

# 解析：
# 05 00 - version 5.0
# 0c - packet type 12 (bind_ack)
# 03 - flags
# 10 00 00 00 - data representation (little endian)
# 3c 00 00 00 - frag length (60 bytes)
# 00 00 00 00 - auth length
# 00 00 00 00 - call id
# 00 10 00 10 - max xmit/recv frag
# 29 a6 00 00 - assoc group
# 06 00 - secondary addr len (6)
# 36 32 38 33 31 00 - "62831\0" (secondary address = port number string)
# 01 00 00 00 - num results
# 02 00 01 00 - result (acceptance) + reason
# 00 00 00 00 00 00 00 00 00 00 00 00 - transfer syntax (zeroed)

# 这表明服务器接受了 UUID: 44c7787d8d4f1b4f8a864962c36ae41f (之前的尝试)
# 实际 UUID: {7d78c744-4f8d-4f1b-8a86-4962c36ae41f}

# 问题可能是超时设置或网络状态

import socket
import struct
import time

TARGET = "116.62.114.4"
PORT = 62831

# 这是之前成功的 bind 请求格式
# UUID: 44c7787d8d4f1b4f8a864962c36ae41f
interface_uuid = bytes.fromhex('44c7787d8d4f1b4f8a864962c36ae41f')

def make_bind():
    ndr_syntax = bytes.fromhex('045d888aeb1cc9119fe808002b104860')
    
    ctx_item = struct.pack('<HBB', 0, 1, 0)
    ctx_item += interface_uuid
    ctx_item += struct.pack('<HH', 1, 0)
    ctx_item += ndr_syntax
    ctx_item += struct.pack('<HH', 2, 0)
    
    bind_body = struct.pack('<HH', 0x16d0, 0x16d0)
    bind_body += struct.pack('<I', 0)
    bind_body += struct.pack('<BBH', 1, 0, 0)
    bind_body += ctx_item
    
    header = struct.pack(
        '<BBBBIHHI',
        5, 0, 11, 0x03,
        0x10, 24 + len(bind_body), 0, 0
    )
    
    return header + bind_body

def make_request(opnum, data):
    req_body = struct.pack('<IHH', len(data), 0, opnum)
    req_body += data
    
    padding = (8 - len(req_body) % 8) % 8
    req_body += b'\x00' * padding
    
    header = struct.pack(
        '<BBBBIHHI',
        5, 0, 0, 0x03,
        0x10, 24 + len(req_body), 0, 1
    )
    
    return header + req_body

def recv_full(sock, timeout=15):
    """持续接收直到超时"""
    sock.settimeout(timeout)
    data = b""
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            sock.settimeout(2)
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            print(f"  Received {len(chunk)} bytes, total {len(data)}")
            
            # 检查是否收到完整的 RPC 响应
            if len(data) >= 10:
                frag_len = struct.unpack('<H', data[8:10])[0]
                if len(data) >= frag_len:
                    print(f"  Complete response received (frag_len={frag_len})")
                    break
        except socket.timeout:
            if data:
                break
            continue
    
    return data

def test_connection():
    print(f"[*] Connecting to {TARGET}:{PORT}")
    
    for attempt in range(3):
        print(f"\n=== Attempt {attempt + 1} ===")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((TARGET, PORT))
            print("[+] Connected")
            
            # 发送 bind
            bind_pdu = make_bind()
            print(f"[*] Sending bind ({len(bind_pdu)} bytes)")
            print(f"    Data: {bind_pdu.hex()}")
            
            sock.send(bind_pdu)
            
            # 接收响应
            print("[*] Waiting for response...")
            resp = recv_full(sock, 20)
            
            if resp:
                print(f"\n[+] Got response ({len(resp)} bytes)")
                print(f"    Hex: {resp.hex()}")
                
                if len(resp) >= 3:
                    ptype = resp[2]
                    print(f"    Packet type: {ptype} ({'bind_ack' if ptype == 12 else 'other'})")
                    
                    if ptype == 12:
                        print("[+] BIND SUCCESSFUL!")
                        
                        # 尝试调用 opnum 0
                        print("\n[*] Trying opnum 0...")
                        req = make_request(0, b'\x00' * 8)
                        sock.send(req)
                        
                        resp2 = recv_full(sock, 10)
                        if resp2:
                            print(f"[*] Response: {resp2.hex()}")
                        
                        return sock
            else:
                print("[-] No response received")
            
            sock.close()
            
        except Exception as e:
            print(f"[-] Error: {e}")
        
        time.sleep(2)
    
    return None

if __name__ == "__main__":
    test_connection()
