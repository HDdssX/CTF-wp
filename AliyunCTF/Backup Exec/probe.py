#!/usr/bin/env python3
"""
探测 Backup Exec 服务和 FTP 服务
"""

import socket
import struct
import sys
import time

TARGET = "116.62.114.4"

def probe_ftp():
    """探测 FTP 服务"""
    print("[*] Probing FTP service on port 21")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((TARGET, 21))
        
        # 接收 banner
        banner = sock.recv(1024)
        print(f"[+] FTP Banner: {banner.decode('utf-8', errors='ignore').strip()}")
        
        # 尝试匿名登录
        sock.send(b"USER anonymous\r\n")
        resp = sock.recv(1024)
        print(f"[*] USER response: {resp.decode('utf-8', errors='ignore').strip()}")
        
        sock.send(b"PASS anonymous@\r\n")
        resp = sock.recv(1024)
        print(f"[*] PASS response: {resp.decode('utf-8', errors='ignore').strip()}")
        
        # 列出目录
        sock.send(b"PASV\r\n")
        resp = sock.recv(1024)
        print(f"[*] PASV response: {resp.decode('utf-8', errors='ignore').strip()}")
        
        sock.close()
    except Exception as e:
        print(f"[-] FTP probe failed: {e}")

def probe_rpc(port):
    """探测 RPC 服务"""
    print(f"\n[*] Probing service on port {port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((TARGET, port))
        
        # 发送 RPC Bind 请求
        # DCE/RPC version 5.0, bind packet
        rpc_header = struct.pack(
            '<BBBBIHH',
            5,      # version major
            0,      # version minor  
            11,     # packet type (bind)
            3,      # packet flags
            16,     # data representation (little endian)
            0,      # frag length (will be updated)
            0       # auth length
        )
        
        # 发送原始数据看响应
        sock.send(b"\x05\x00\x0b\x03\x10\x00\x00\x00\x48\x00\x00\x00\x00\x00\x00\x00\xd0\x16\xd0\x16\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x00")
        sock.settimeout(5)
        try:
            resp = sock.recv(4096)
            print(f"[+] Response ({len(resp)} bytes): {resp[:100].hex()}")
            if resp:
                print(f"[+] Raw: {resp[:50]}")
        except socket.timeout:
            print("[-] No response (timeout)")
        
        sock.close()
    except Exception as e:
        print(f"[-] RPC probe on port {port} failed: {e}")

def probe_raw(port):
    """发送空数据并接收响应"""
    print(f"\n[*] Raw probe on port {port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((TARGET, port))
        
        # 等待服务器主动发送数据
        sock.settimeout(3)
        try:
            banner = sock.recv(4096)
            print(f"[+] Banner ({len(banner)} bytes): {banner[:200]}")
            print(f"[+] Hex: {banner[:50].hex()}")
        except socket.timeout:
            print("[-] Server didn't send banner, trying to send data...")
            
            # 发送一些测试数据
            sock.send(b"HELLO\r\n")
            try:
                resp = sock.recv(4096)
                print(f"[+] Response: {resp[:200]}")
            except:
                print("[-] No response")
        
        sock.close()
    except Exception as e:
        print(f"[-] Raw probe on port {port} failed: {e}")

if __name__ == "__main__":
    probe_ftp()
    probe_rpc(62831)
    probe_raw(62831)
