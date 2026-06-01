import base64
import re
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, "_deps")
import gmpy2


HOST = "1.95.113.92"
PORT = 9999
MOD = gmpy2.mpz(2) ** 1279 - 1


def b64d_int(s: str) -> gmpy2.mpz:
    return gmpy2.mpz(int.from_bytes(base64.b64decode(s), "big"))


def b64e_int(v: gmpy2.mpz) -> str:
    n = int(v)
    size = (n.bit_length() // 24) * 3 + 3
    raw = n.to_bytes(size, "big")
    return base64.b64encode(raw).decode()


def solve_token(token: str) -> str:
    kind, diff_s, challenge_s = token.strip().split(".")
    if kind != "s":
        raise ValueError(f"unsupported POW kind {kind!r}")
    diff = int(b64d_int(diff_s))
    x = b64d_int(challenge_s)
    exp = gmpy2.mpz(2) ** 1277
    start = time.time()
    for i in range(diff):
        x = gmpy2.powmod(x, exp, MOD).bit_flip(0)
        if i and i % 50000 == 0:
            print(f"pow {i}/{diff} {time.time() - start:.1f}s", flush=True)
    print(f"pow done {diff} rounds in {time.time() - start:.1f}s", flush=True)
    return "s." + b64e_int(x)


def verify_token(challenge: str, solution: str) -> bool:
    _, diff_s, challenge_s = challenge.strip().split(".")
    _, solution_s = solution.strip().split(".")
    diff = int(b64d_int(diff_s))
    y = b64d_int(solution_s)
    for _ in range(diff):
        y = (y.bit_flip(0) ** 2) % MOD
    return y == b64d_int(challenge_s)


def recv_until(sock: socket.socket, marker: bytes, timeout: float = 10.0) -> bytes:
    sock.settimeout(timeout)
    data = b""
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "solve":
        print(solve_token(sys.argv[2]))
        return
    if len(sys.argv) >= 4 and sys.argv[1] == "verify":
        print(verify_token(sys.argv[2], sys.argv[3]))
        return

    with socket.create_connection((HOST, PORT), timeout=10) as sock:
        banner = recv_until(sock, b"Solution? ", timeout=10)
        print(banner.decode(errors="replace"), end="")
        m = re.search(rb"\bs\.[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+", banner)
        if not m:
            raise RuntimeError("no pow token found")
        sol = solve_token(m.group(0).decode())
        print(f"solution={sol}", flush=True)
        sock.sendall(sol.encode() + b"\n")
        capture = bytearray()
        sock.settimeout(30)
        while True:
            try:
                chunk = sock.recv(65536)
            except TimeoutError:
                break
            if not chunk:
                break
            capture.extend(chunk)
        out = Path("server_payload.txt")
        out.write_bytes(bytes(capture))
        print(f"captured {len(capture)} bytes to {out}")


if __name__ == "__main__":
    main()
