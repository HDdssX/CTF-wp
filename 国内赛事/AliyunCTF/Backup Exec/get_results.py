#!/usr/bin/env python3
"""
读取 results.txt 文件
"""

import socket
import re

TARGET = "116.62.114.4"

def ftp_get_file(filepath):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((TARGET, 21))
    
    # 接收 banner
    sock.recv(1024)
    
    # 登录
    sock.send(b"USER anonymous\r\n")
    sock.recv(1024)
    sock.send(b"PASS test@test.com\r\n")
    sock.recv(1024)
    
    # 进入目录
    sock.send(b"CWD microsoft\r\n")
    sock.recv(1024)
    
    # PASV
    sock.send(b"PASV\r\n")
    resp = sock.recv(1024).decode()
    
    match = re.search(r'\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)', resp)
    if match:
        nums = [int(x) for x in match.groups()]
        port = nums[4] * 256 + nums[5]
        
        # 数据连接
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.settimeout(30)
        data_sock.connect((TARGET, port))
        
        # TYPE I
        sock.send(b"TYPE I\r\n")
        sock.recv(1024)
        
        # RETR
        sock.send(f"RETR {filepath}\r\n".encode())
        sock.recv(1024)
        
        # 接收文件
        content = b""
        while True:
            try:
                chunk = data_sock.recv(8192)
                if not chunk:
                    break
                content += chunk
            except:
                break
                
        data_sock.close()
        sock.recv(1024)
        
        return content
    
    return None

content = ftp_get_file("results.txt")
if content:
    print(f"[+] Downloaded {len(content)} bytes")
    print("\n" + "="*60)
    print(content.decode('utf-8', errors='ignore')[:10000])
    print("="*60)
    
    # 保存到本地
    with open(r"F:\CTF\CTF-wp\AliyunCTF\Backup Exec\results.txt", "wb") as f:
        f.write(content)
    print("\n[+] Saved to results.txt")
