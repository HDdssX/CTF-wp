#!/usr/bin/env python3
"""
Backup Exec File Daemon RPC Client
纯 socket 实现
"""

import socket
import struct
import sys

TARGET = "116.62.114.4"
PORTS = [69128, 62831, 67540, 60325, 63588, 135, 21]

def test_port(target, port, timeout=5):
    """测试端口连通性"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        if result == 0:
            # 尝试接收 banner
            try:
                sock.settimeout(2)
                banner = sock.recv(1024)
                sock.close()
                return True, banner
            except:
                sock.close()
                return True, b""
        sock.close()
        return False, b""
    except Exception as e:
        return False, str(e).encode()

def main():
    print(f"[*] Testing connectivity to {TARGET}")
    print("=" * 50)
    
    for port in PORTS:
        is_open, banner = test_port(TARGET, port)
        status = "OPEN" if is_open else "CLOSED"
        print(f"Port {port}: {status}")
        if banner:
            print(f"  Banner: {banner[:200]}")

if __name__ == "__main__":
    main()
