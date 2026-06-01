# PCB5-ez_java 项目源码还原

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
