# CTF Web Challenge Analysis: pcb5-ez_java

## 1. 环境信息
- **URL**: `http://192.168.18.25:25004`
- **架构**: Apache (Reverse Proxy/Rewrite) + Tomcat (Java/JSP)
- **功能**: 登录/注册、文件管理 Dashboard (上传、下载、列表)

## 2. 重大突破！成功绕过WEB-INF保护

### 路径遍历绕过方法
**关键发现**：使用URL编码绕过路径检查！

成功的payload：
```
/download?path=uploads%2f..%2fWEB-INF%2fweb.xml
```

**原理**：
1. Rewrite规则：`RewriteRule ^/download$ /%2 [B,L]`
2. `[B]` flag会对backreference进行URL解码处理
3. `uploads%2f..%2fWEB-INF%2fweb.xml` → `uploads/../WEB-INF/web.xml` → `WEB-INF/web.xml`

### 成功读取的敏感文件

#### A. WEB-INF/web.xml
发现5个Servlet：
1. **LoginServlet** - `/login`
2. **RegisterServlet** - `/register`  
3. **DashboardServlet** - `/dashboard/*`
4. **AdminDashboardServlet** - `/admin/*` ⭐ 新发现！
5. **BackUpServlet** - `/backup/*` ⭐ 新发现！

#### B. Java Class文件
成功下载并反编译了所有Servlet的class文件：
- `LoginServlet.class`
- `RegisterServlet.class`
- `DashboardServlet.class`
- `AdminDashboardServlet.class` 
- `BackUpServlet.class`

### BackUpServlet分析

从反编译的代码中发现：
1. **需要key参数**：key存储在webapp父目录的`??.key`文件中
2. **两个功能**：
   - `/backup/tar?key=XXX` - 将uploads目录打包为tar
   - `/backup/untar?key=XXX` - 将backup/out.tar解包到uploads

## 3. 当前状态和下一步

### 已验证的漏洞
1. ✅ 任意文件读取（通过URL编码绕过）
2. ✅ 可读取WEB-INF目录
3. ✅ 可下载Java class文件
4. ❌ uploads目录中的JSP无法执行

### 待探索
1. **找到backup key**：
   - Key文件名未知（显示为`??.key`）
   - 位置：webapp父目录
   - 需要猜测文件名或查找其他线索

2. **利用AdminDashboardServlet**：
   - 需要admin权限（返回401）
   - 可能需要通过JWT token提权

3. **继续探索文件系统**：
   - 尝试读取更多配置文件
   - 查找flag的可能位置

### 可能的攻击路径
1. **路径1**：找到backup key → 使用backup功能 → 可能触发某些特殊操作
2. **路径2**：分析AdminDashboardServlet.class → 找到提权方法 → 访问admin功能
3. **路径3**：继续探索文件系统 → 直接找到flag文件

## 4. 使用的Payload

### 读取WEB-INF文件
```
GET /download?path=uploads%2f..%2fWEB-INF%2fweb.xml
GET /download?path=uploads%2f..%2fWEB-INF%2fclasses%2fcom%2fctf%2fBackUpServlet.class
```

### API端点
```
GET /dashboard/list - 列出上传的文件
GET /dashboard/stats - 统计信息
GET /dashboard/recent - 最近上传的文件
GET /admin/* - 需要admin权限（401）
GET /backup/* - 需要key参数（400）
```
