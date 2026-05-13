# LilacCTF - Keep 题解

## 题目概览

*   **题目类型**: Web
*   **核心漏洞**: PHP Built-in Server Source Code Disclosure (PHP内置服务器源码泄露), HTTP Pipelining, Request Smuggling
*   **Flag**: `cyberpeace{5aa1f5a0813816e00ceca528fbb7b18f}`

## 解题步骤

### 1. 发现源码泄露漏洞

题目环境是一个 PHP 应用。通过提供的初始脚本 `exp.py` 我们发现，通过构造 HTTP Pipelining 请求，可以触发 PHP 内置开发服务器的一个已知 BUG，导致 PHP 源码被直接返回而不是执行。

核心 Payload 原理如下：
```http
GET /index.php HTTP/1.1
Host: target
(空行)
GET /xyz.xyz HTTP/1.1
(空行)
```
当服务器接收到这种连续请求时，处理逻辑出现竞态条件，导致 `index.php` 被当作静态文件输出。

### 2. 信息收集：获取 hidden file

利用上述漏洞读取 `index.php` 源码：

```php
<?php
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             