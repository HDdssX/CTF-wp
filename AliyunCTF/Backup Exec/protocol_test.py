#!/usr/bin/env python3
"""
更仔细地分析 Backup Exec 协议
"""

import socket
import struct
import time

TARGET = "116.62.114.4"
PORT = 62831

def send_and_recv(sock, data, description="", timeout=5):
    """发送数据并接收响应"""
    print(f"\n[*] {description}")
    print(f"    Sending ({len(data)} bytes): {data.hex()}")
    
    sock.send(data)
    sock.settimeout(timeout)
    
    try:
        resp = sock.recv(4096)
        print(f"    Received ({len(resp)} bytes): {resp.hex()}")
        
        # 尝试解码
        try:
            text = resp.decode('utf-8', errors='ignore')
            printable = ''.join(c if c.isprintable() else '.' for c in text)
            print(f"    ASCII: {printable[:100]}")
        except:
            pass
        
        return resp
    except socket.timeout:
        print("    No response (timeout)")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None

def test_protocol():
    """测试不同的协议格式"""
    
    # 首先检查这是否是标准的 DCE/RPC 服务
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    print(f"[+] Connected to {TARGET}:{PORT}")
    
    # 测试1: 等待服务器 banner
    print("\n[*] Waiting for server banner...")
    sock.settimeout(3)
    try:
        banner = sock.recv(1024)
        print(f"    Banner: {banner.hex()}")
    except socket.timeout:
        print("    No banner")
    
    sock.close()
    time.sleep(1)
    
    # 测试2: 标准 RPC bind
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    
    # 从之前成功的响应分析：
    # 05000c03100000003c000000000000000010001029a600000600363238333100010000000200010000000000000000000000
    # 这是一个 bind_ack 响应
    # 05 00 = version 5.0
    # 0c = packet type 12 (bind_ack)
    # 03 = flags
    # 10 = data rep (LE)
    # 00 00 00 3c = frag length 60
    
    # 让我尝试之前成功的 bind 数据
    bind_data = bytes.fromhex(
        '05000b0310000000480000000000000000001000' +  # RPC header
        'd016d0160000000001000000' +                  # bind body start
        '00000100'                                     # context items
    )
    
    # 完整的 bind 请求 - 让我构造一个正确的
    interface_uuid = bytes.fromhex('44c7787d8d4f1b4f8a864962c36ae41f')  # 这个之前成功了
    ndr_syntax = bytes.fromhex('045d888aeb1cc9119fe808002b104860')
    
    # 构造 bind PDU
    ctx_item = struct.pack('<HBB', 0, 1, 0)  # context_id=0, num_items=1
    ctx_item += interface_uuid
    ctx_item += struct.pack('<HH', 1, 0)  # version 1.0
    ctx_item += ndr_syntax
    ctx_item += struct.pack('<HH', 2, 0)  # NDR version 2.0
    
    bind_body = struct.pack('<HH', 0x1000, 0x1000)  # max xmit/recv
    bind_body += struct.pack('<I', 0)  # assoc group
    bind_body += struct.pack('<BBH', 1, 0, 0)  # p_cont_elem
    bind_body += ctx_item
    
    header = struct.pack(
        '<BBBBIHHI',
        5, 0,     # version
        11,       # bind
        0x03,     # flags (first+last)
        0x10,     # data rep
        24 + len(bind_body),  # frag length
        0,        # auth length
        0         # call id
    )
    
    full_bind = header + bind_body
    
    resp = send_and_recv(sock, full_bind, "Standard RPC Bind", 10)
    
    if resp and len(resp) >= 3:
        ptype = resp[2]
        print(f"    Packet type: {ptype}")
        
        if ptype == 12:  # bind_ack
            print("[+] Bind successful!")
            
            # 尝试调用方法
            for opnum in range(0, 5):
                req_body = struct.pack('<IHH', 16, 0, opnum)  # alloc_hint, ctx_id, opnum
                req_body += b'\x00' * 16  # dummy data
                
                # 8字节对齐
                padding = (8 - len(req_body) % 8) % 8
                req_body += b'\x00' * padding
                
                req_header = struct.pack(
                    '<BBBBIHHI',
                    5, 0, 0, 0x03, 0x10,
                    24 + len(req_body),
                    0, opnum + 1
                )
                
                request = req_header + req_body
                resp = send_and_recv(sock, request, f"RPC Request opnum={opnum}", 5)
                
                if resp:
                    # 检查响应类型
                    if len(resp) >= 3:
                        resp_type = resp[2]
                        print(f"    Response type: {resp_type}")
    
    sock.close()

if __name__ == "__main__":
    test_protocol()
