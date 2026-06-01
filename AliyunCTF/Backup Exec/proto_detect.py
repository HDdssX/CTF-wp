#!/usr/bin/env python3
"""
协议探测 - 检测 62831 端口使用的协议
"""

import socket
import struct
import time

TARGET = "116.62.114.4"
PORT = 62831

def test_connection(data, desc):
    """发送数据并接收响应"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((TARGET, PORT))
        
        if data:
            sock.send(data)
        
        # 等待响应
        time.sleep(1)
        sock.settimeout(5)
        
        response = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass
        
        sock.close()
        
        print(f"{desc}:")
        if response:
            print(f"  Response ({len(response)} bytes): {response[:100]}")
            print(f"  Hex: {response[:60].hex()}")
        else:
            print("  No response")
        print()
        return response
        
    except Exception as e:
        print(f"{desc}: Error - {e}\n")
        return None

# 测试 1: 空连接
print("="*60)
print(f"Protocol Detection for {TARGET}:{PORT}")
print("="*60)
print()

# 测试 1: 等待服务端先说话 (banner)
print("Test 1: Wait for banner...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, PORT))
    sock.settimeout(5)
    
    try:
        banner = sock.recv(4096)
        print(f"  Banner: {banner}")
        print(f"  Hex: {banner.hex()}" if banner else "No banner")
    except socket.timeout:
        print("  No banner (server waits for client)")
    
    sock.close()
except Exception as e:
    print(f"  Error: {e}")

print()

# 测试 2: HTTP
test_connection(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n", "Test 2: HTTP")

# 测试 3: SSL/TLS ClientHello
tls_hello = bytes.fromhex(
    '160301'  # TLS record: handshake, TLS 1.0
    '0200'    # length placeholder (will be minimal)
    '01'      # ClientHello
    '000000'  # length
)
test_connection(tls_hello, "Test 3: TLS")

# 测试 4: SMB/NetBIOS
smb_nego = bytes.fromhex(
    '00000054'  # NetBIOS session message
    'ff534d42'  # SMB magic
    '72'        # Negotiate protocol
    '00000000'  # status
    '18'        # flags
    '5300'      # flags2
    '0000000000000000'  # pid
    '0000000000000000'  # tid
    '0000'      # uid
    '0000'      # mid
    '00'        # word count
    '1100'      # byte count
    '02'        # dialect
    '4e54204c4d20302e313200'  # NT LM 0.12
)
test_connection(smb_nego, "Test 4: SMB")

# 测试 5: RPC version probe
rpc_probe = struct.pack('<BBBBIHHI',
    5, 0,      # version 5.0
    11,        # bind
    0x03,      # flags
    0x10,      # data rep
    24,        # minimal frag length (just header)
    0, 0       # auth length, call id
)
test_connection(rpc_probe, "Test 5: Minimal RPC bind")

# 测试 6: MS-RPC bind with MGMT UUID (管理接口，通常都支持)
mgmt_uuid = bytes.fromhex('afa8bd9087ce1311aad5108002b2e6f0')  # mgmt interface
ndr_syntax = bytes.fromhex('045d888aeb1cc9119fe808002b104860')

ctx_item = struct.pack('<HBB', 0, 1, 0)
ctx_item += mgmt_uuid
ctx_item += struct.pack('<HH', 1, 0)
ctx_item += ndr_syntax + struct.pack('<HH', 2, 0)

bind_body = struct.pack('<HH', 0x1000, 0x1000)
bind_body += struct.pack('<I', 0)
bind_body += struct.pack('<BBH', 1, 0, 0)
bind_body += ctx_item

frag_length = 24 + len(bind_body)
header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, frag_length, 0, 0)
mgmt_bind = header + bind_body
test_connection(mgmt_bind, "Test 6: RPC MGMT interface")

# 测试 7: 简单文本
test_connection(b"HELLO\r\n", "Test 7: Plain text")

# 测试 8: JSON
test_connection(b'{"command":"read","path":"C:\\\\flag.txt"}\n', "Test 8: JSON")

# 测试 9: XML
test_connection(b'<?xml version="1.0"?><request><read>flag.txt</read></request>', "Test 9: XML")

# 测试 10: 自定义二进制 - 长度前缀协议
# 假设协议是: [4字节长度][命令]
custom1 = struct.pack('<I', 4) + b'READ'
test_connection(custom1, "Test 10: Length-prefixed (READ)")

# 测试 11: 从结果文件中的 FTP 端口获取灵感
# FTP 通过端口 21，而数据在特定端口
# 也许 62831 是一个自定义的简单协议
test_connection(b"RETR flag.txt\r\n", "Test 11: FTP-like RETR")

# 测试 12: 尝试发送路径
test_connection(b"C:\\Users\\Administrator\\Desktop\\flag.txt\r\n", "Test 12: Raw path")

# 测试 13: 空字节开头
test_connection(b"\x00\x00\x00\x00flag.txt", "Test 13: Null bytes + path")

# 测试 14: BEFD 特定协议 - 可能需要特定的 magic
# 搜索二进制中的 magic bytes
test_connection(b"BEFD", "Test 14: BEFD magic")
test_connection(b"\xbe\xfd", "Test 15: BEFD bytes")

# 测试 16: 更多 magic
test_connection(b"NDMP", "Test 16: NDMP (Network Data Management Protocol)")
