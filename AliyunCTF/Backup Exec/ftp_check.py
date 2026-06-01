#!/usr/bin/env python3
"""
仔细检查 FTP 服务器上的所有文件
"""

import socket
import re

TARGET = "116.62.114.4"

def ftp_cmd(sock, cmd):
    sock.send((cmd + "\r\n").encode())
    sock.settimeout(5)
    try:
        return sock.recv(4096).decode('utf-8', errors='ignore')
    except socket.timeout:
        return ""

def ftp_list(sock, path="."):
    # PASV
    resp = ftp_cmd(sock, "PASV")
    match = re.search(r'\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)', resp)
    if not match:
        return ""
    
    nums = [int(x) for x in match.groups()]
    port = nums[4] * 256 + nums[5]
    
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.settimeout(10)
    data_sock.connect((TARGET, port))
    
    ftp_cmd(sock, f"CWD {path}")
    ftp_cmd(sock, "LIST -la")
    
    listing = b""
    while True:
        try:
            chunk = data_sock.recv(4096)
            if not chunk:
                break
            listing += chunk
        except:
            break
    
    data_sock.close()
    sock.recv(1024)  # 清除响应
    
    return listing.decode('utf-8', errors='ignore')

def ftp_get(sock, filepath):
    # PASV
    resp = ftp_cmd(sock, "PASV")
    match = re.search(r'\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)', resp)
    if not match:
        return None
    
    nums = [int(x) for x in match.groups()]
    port = nums[4] * 256 + nums[5]
    
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.settimeout(10)
    data_sock.connect((TARGET, port))
    
    ftp_cmd(sock, "TYPE I")
    resp = ftp_cmd(sock, f"RETR {filepath}")
    
    if "550" in resp:
        data_sock.close()
        return None
    
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

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((TARGET, 21))
    
    # Banner
    print(sock.recv(1024).decode())
    
    # Login
    ftp_cmd(sock, "USER anonymous")
    ftp_cmd(sock, "PASS test@")
    
    print("[*] Root directory:")
    print(ftp_list(sock, "/"))
    
    print("\n[*] Microsoft directory:")
    print(ftp_list(sock, "microsoft"))
    
    # 检查是否有其他隐藏文件
    print("\n[*] Checking for hidden files...")
    
    # 读取所有能读取的文件
    files = [
        "silconfig.log",
        "AliyunAssistClientSingleLock.lock",
        "FXSAPIDebugLogFile.txt",
        "FXSTIFFDebugLogFile.txt",
        "microsoft/results.txt",
        "flag.txt",
        ".flag.txt",
        "microsoft/flag.txt",
        "microsoft/.flag.txt",
    ]
    
    for f in files:
        content = ftp_get(sock, f)
        if content:
            print(f"\n=== {f} ({len(content)} bytes) ===")
            # 只显示前500字节
            print(content[:500])
    
    # 搜索 results.txt 中的 flag
    print("\n[*] Searching for 'flag' in results.txt...")
    content = ftp_get(sock, "microsoft/results.txt")
    if content:
        text = content.decode('utf-8', errors='ignore')
        if 'flag' in text.lower():
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'flag' in line.lower():
                    print(f"Line {i}: {line.strip()}")
        
        # 也搜索 aliyun
        if 'aliyun' in text.lower():
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'aliyun' in line.lower():
                    print(f"Line {i}: {line.strip()}")
    
    sock.close()

if __name__ == "__main__":
    main()
