# AliyunCTF 2026 - next-challenge Writeup

## 题目信息

- **题目名称**: next-challenge
- **类型**: Web
- **描述**: next WAF
- **环境**: Node.js v20.19.6 Alpine x64
- **目标**: http://223.6.249.127:41904

## 初步分析

### 1. 获取源码

访问目标后，发现可以下载源码包 `/source-3527c84d-2ecc-4c76-9d83-7e83138c19a8.zip`

### 2. 技术栈识别

从 `package.json` 分析：
- **Next.js**: 16.0.6
- **React**: 19.2.0
- **Node.js**: v20.19.6 Alpine

### 3. 架构分析

```
用户请求 → WAF (Python Flask, port 8080) → Next.js (port 3000)
```

## WAF 分析

### WAF 代码 (waf.py)

```python
FORBIDDEN_KEYWORDS = ["__proto__", "constructor", "prototype", "\\u"]
```

WAF 的关键逻辑：

1. **text/plain 请求**:
   - `json.loads(body)` 解析请求体
   - `check_forbidden(parsed)` 检查敏感关键字
   - 转发**原始** body 给后端

2. **multipart/form-data 请求**:
   - 遍历所有字段，`json.loads(value)` 解析
   - `check_forbidden(data)` 检查
   - `json.dumps(data)` **重新序列化**后转发

3. **check_forbidden 函数**:
   - 递归检查所有字符串值
   - 检查所有对象的 key
   - 如果字符串是有效 JSON，会递归解析并检查
   - 检查使用 `value.lower()` 进行大小写不敏感匹配

### WAF 拦截的关键字
- `__proto__` - 原型污染核心
- `constructor` - 另一种原型访问方式
- `prototype` - 原型链
- `\u` - Unicode 转义（防止编码绕过）

## 漏洞识别

### CVE-2025-55182 (CVSS 10.0)

**React Server Components (RSC) 原型污染导致 RCE**

漏洞描述：React 的 RSC Flight 协议反序列化器在处理对象时没有使用 `hasOwnProperty` 检查，导致攻击者可以通过 `__proto__` 键污染 `Object.prototype`。

漏洞版本：React 19.x (19.2.0 受影响)

## Server Action 分析

### 发现 Server Action

从源码 `actions.ts` 发现：

```typescript
"use server";

export async function Hello(input: string) {
  return `hello ${input}!`;
}
```

### Server Action ID

通过测试确定 Action ID: `401da4050210f37f7fa7a9507207e6ca489478998d`

### 基本通信验证

```python
import requests

TARGET = "http://223.6.249.127:52324/"
ACTION_ID = "401da4050210f37f7fa7a9507207e6ca489478998d"

headers = {
    "Next-Action": ACTION_ID,
    "Content-Type": "text/plain;charset=UTF-8"
}
payload = '["test"]'
resp = requests.post(TARGET, headers=headers, data=payload)
# 响应: "hello test!"
```

## RSC Flight 协议研究

### $ 前缀类型系统

通过大量测试，发现 RSC Flight 协议支持的特殊类型：

| 前缀 | 类型 | 示例 |
|------|------|------|
| `$undefined` | undefined | `["$undefined"]` → `undefined` |
| `$NaN` | NaN | `["$NaN"]` → `NaN` |
| `$Infinity` | Infinity | `["$Infinity"]` → `Infinity` |
| `$-Infinity` | -Infinity | `["$-1"]` → `-Infinity` |
| `$$` | 转义 $ | `["$$test"]` → `$test` |
| `$@n` | Promise 引用 | `["$@0"]` → `[object Promise]` |
| `$Rn` | ReadableStream | `["$R0"]` → `[object ReadableStream]` |
| `$Wn` | Set (引用字段n) | `["$W0"]` → `[object Set]` |
| `$Qn` | Map (引用字段n) | `["$Q1"]` → `[object Map]` |
| `$Xn` | Object | `["$X0"]` → `[object Object]` |
| `$Kn` | FormData | `["$K0"]` → `[object FormData]` |
| `$Dn` | Date | `["$D0"]` → Date对象 |
| `$Bn` | Blob/Buffer | `["$B0"]` → 部分解析 |
| `$nn` | Number | `["$n0"]` → `0` |
| `$In` | Infinity | `["$I0"]` → `Infinity` |
| `$Nn` | NaN | `["$N0"]` → `NaN` |

### Multipart 引用机制

使用 multipart 时，可以在不同字段之间建立引用：

```python
# 字段 0 引用字段 1 的 Map
fields = {
    "0": '["$Q1"]',
    "1": '[["key", "value"]]'
}
# 结果: [object Map]
```

## WAF 绕过尝试

### 1. Unicode 转义绕过 ❌

```python
# 尝试用 \uXXXX 编码 __proto__
payload = '[{"\\u005f\\u005f\\u0070\\u0072\\u006f\\u0074\\u006f\\u005f\\u005f": "test"}]'
# 结果: WAF 检查解析后的值，仍然检测到 __proto__
```

**失败原因**: WAF 先 `json.loads` 解析，`\u005f` 变成 `_`，然后检查解码后的 `__proto__`

### 2. 大小写绕过 ❌

```python
payload = '[{"__PROTO__": "test"}]'
# 结果: WAF 使用 .lower() 检查，大小写不敏感
```

### 3. Unicode 替代字符 ❌

```python
# 使用 Unicode 下划线替代 _
# ＿ (U+FF3F) - 全角下划线
payload = '[{"＿＿proto＿＿": "test"}]'
# 结果: 通过 WAF，但 JavaScript 不认识这个键名
```

### 4. $$ 转义机制 ❌

```python
# $$ 在 RSC 中转义为 $
payload = '["$$__proto__"]'
# 结果: WAF 在 RSC 解析前检查原始字符串，检测到 __proto__
```

### 5. 字符串分割 ❌

```python
# 尝试用 multipart 分割关键字
# 希望: "__" + "proto" + "__" 被拼接
# 结果: RSC 不支持字符串拼接
```

### 6. __defineGetter__ 等方法 ✓ (通过WAF，但无法利用)

```python
payload = '[{"__defineGetter__": "test"}]'
# 结果: 通过 WAF! 但不是直接的原型污染
```

**发现**: `__defineGetter__`, `__defineSetter__`, `__lookupGetter__`, `__lookupSetter__` 不在 WAF 黑名单中

### 7. Content-Type 大小写 ❌

```python
# WAF 对 Content-Type 大小写敏感
headers = {"Content-Type": "Text/Plain"}
# 结果: 400 错误，WAF 只接受小写 "text/plain"
```

### 8. HTTP 参数污染 ❌

```python
# 发送重复字段名
# 字段1: ["safe"]
# 字段2: ["malicious"]
# 结果: WAF 检查所有值，然后只转发最后一个
```

### 9. Chunked 编码 ❌

```python
# 使用 Transfer-Encoding: chunked
# 结果: WAF 正常处理，无法绕过
```

### 10. UTF-7 编码 ❌

```python
headers = {"Content-Type": "text/plain;charset=utf-7"}
# 结果: 服务器接受，但 JSON 解析仍按 UTF-8
```

## 当前状态

### 已确认的信息

1. ✅ CVE-2025-55182 漏洞存在于 React 19.2.0
2. ✅ Server Action 通信正常工作
3. ✅ WAF 设计严密，检查解析后的值
4. ✅ RSC $ 类型系统已基本映射
5. ✅ `__defineGetter__` 等方法可绕过 WAF

### 未解决的问题

1. ❌ 无法绕过 `__proto__` 关键字过滤
2. ❌ 无法绕过 `constructor` 关键字过滤
3. ❌ 无法绕过 `prototype` 关键字过滤
4. ❌ 无法绕过 `\u` 关键字过滤

## 可能的攻击方向

### 方向 1: 寻找 WAF 和 RSC 解析器的差异

WAF 使用 Python `json.loads`，RSC 使用自定义解析器。如果两者对某些边界情况处理不同，可能存在绕过机会。

### 方向 2: 利用 RSC 其他漏洞

除了 `__proto__` 污染，RSC 可能存在其他攻击向量，例如：
- 特殊 $ 前缀的未知行为
- 引用机制的滥用
- 类型混淆

### 方向 3: 利用 `__defineGetter__` 等方法

这些方法绕过了 WAF，但需要研究是否能通过 RSC 反序列化器触发有害行为。

### 方向 4: HTTP 层攻击

- HTTP Request Smuggling
- 利用 WAF 和后端的 HTTP 解析差异

## 测试脚本

已创建的测试脚本（exploit1.py - exploit24.py）涵盖：

1. 基本通信测试
2. Unicode 编码绕过
3. RSC 类型系统探索
4. Multipart 引用机制
5. WAF 逻辑分析
6. HTTP 层攻击尝试

## 待继续研究

1. 深入研究 React RSC Flight 协议源码
2. 寻找 WAF 检查的盲点
3. 研究是否有其他 CVE 可利用
4. 考虑组合攻击（多个小漏洞组合）

---

**状态**: 🔄 进行中

**最后更新**: 2026-01-31
