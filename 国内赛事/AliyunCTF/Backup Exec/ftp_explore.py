#!/usr/bin/env python3
"""
深入探索 FTP 目录结构
"""

import socket
import re

TARGET = "116.62.114.4"

class FTPClient:
    def __init__(self, host, port=21):
        self.host = host
        self.port = port
        self.sock = None
        
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((self.host, self.port))
        return self.recv()
        
    def send(self, cmd):
        print(f">>> {cmd}")
        self.sock.send((cmd + "\r\n").encode())
        return self.recv()
        
    def recv(self):
        self.sock.settimeout(3)
        data = b""
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                lines = data.decode('utf-8', errors='ignore').split('\r\n')
                if len(lines) >= 2 and lines[-2] and len(lines[-2]) >= 4:
                    if lines[-2][3] == ' ':
                        break
        except socket.timeout:
            pass
        resp = data.decode('utf-8', errors='ignore')
        if resp:
            for line in resp.strip().split('\n'):
                print(f"<<< {line.strip()}")
        return resp
        
    def parse_pasv(self, resp):
        match = re.search(r'\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)', resp)
        if match:
            nums = [int(x) for x in match.groups()]
            port = nums[4] * 256 + nums[5]
            return port
        return None
        
    def list_dir(self, path="."):
        resp = self.send(f"CWD {path}")
        resp = self.send("PASV")
        port = self.parse_pasv(resp)
        
        if port:
            try:
                data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_sock.settimeout(10)
                data_sock.connect((self.host, port))
                
                resp = self.send("LIST -la")  # 尝试显示隐藏文件
                
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
                self.recv()
                
                return listing.decode('utf-8', errors='ignore')
                
            except Exception as e:
                print(f"[-] Error: {e}")
                
        return None
        
    def get_file(self, filepath):
        resp = self.send("PASV")
        port = self.parse_pasv(resp)
        
        if port:
            try:
                data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_sock.settimeout(10)
                data_sock.connect((self.host, port))
                
                self.send("TYPE I")
                resp = self.send(f"RETR {filepath}")
                
                if "150" in resp or "125" in resp:
                    content = b""
                    while True:
                        try:
                            chunk = data_sock.recv(4096)
                            if not chunk:
                                break
                            content += chunk
                        except:
                            break
                            
                    data_sock.close()
                    self.recv()
                    return content
                    
            except Exception as e:
                print(f"[-] Error: {e}")
                
        return None

def main():
    ftp = FTPClient(TARGET)
    
    print("[*] Connecting...")
    ftp.connect()
    ftp.send("USER anonymous")
    ftp.send("PASS test@test.com")
    
    print("\n[*] Exploring directory structure...")
    
    # 列出根目录
    print("\n=== Root directory ===")
    listing = ftp.list_dir("/")
    if listing:
        print(listing)
    
    # 进入 microsoft 目录
    print("\n=== microsoft directory ===")
    listing = ftp.list_dir("microsoft")
    if listing:
        print(listing)
    
    # 递归探索
    def explore(path, depth=0):
        if depth > 3:
            return
            
        ftp.send(f"CWD {path}")
        resp = ftp.send("PASV")
        port = ftp.parse_pasv(resp)
        
        if port:
            try:
                data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_sock.settimeout(5)
                data_sock.connect((ftp.host, port))
                
                ftp.send("LIST")
                
                listing = b""
                try:
                    while True:
                        chunk = data_sock.recv(4096)
                        if not chunk:
                            break
                        listing += chunk
                except:
                    pass
                    
                data_sock.close()
                ftp.recv()
                
                listing_str = listing.decode('utf-8', errors='ignore')
                print(f"\n{'  '*depth}=== {path} ===")
                for line in listing_str.strip().split('\n'):
                    if line.strip():
                        print(f"{'  '*depth}{line.strip()}")
                        # 如果是目录，递归
                        if '<DIR>' in line:
                            dirname = line.strip().split()[-1]
                            if dirname not in ['.', '..']:
                                explore(dirname, depth + 1)
                                ftp.send(f"CWD ..")  # 返回上级
                                
            except Exception as e:
                print(f"{'  '*depth}Error: {e}")
    
    ftp.send("CWD /")
    explore(".", 0)
    
    # 尝试读取可能存在的文件
    print("\n\n[*] Trying to read specific files...")
    files_to_try = [
        "silconfig.log",
        "AliyunAssistClientSingleLock.lock",
        "FXSAPIDebugLogFile.txt",
        "FXSTIFFDebugLogFile.txt",
        "microsoft/flag.txt",
        "flag.txt",
    ]
    
    for f in files_to_try:
        print(f"\n--- Trying {f} ---")
        content = ftp.get_file(f)
        if content:
            print(f"Content ({len(content)} bytes):")
            print(content[:500])

if __name__ == "__main__":
    main()
