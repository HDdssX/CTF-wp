from __future__ import annotations

from math import gcd
from pathlib import Path
from typing import Iterable


BIN = Path(__file__).with_name("echoes-of-regret")
BASE = 0x400000


def u32(x: int) -> int:
    return x & 0xFFFFFFFF


def rol32(x: int, n: int) -> int:
    n &= 31
    return u32((x << n) | (x >> (32 - n)))


def ror32(x: int, n: int) -> int:
    n &= 31
    return u32((x >> n) | (x << (32 - n)))


def rol8(x: int, n: int) -> int:
    n &= 7
    return ((x << n) | (x >> (8 - n))) & 0xFF if n else x & 0xFF


def read(addr: int, size: int) -> bytes:
    blob = BIN.read_bytes()
    return blob[addr - BASE : addr - BASE + size]


def dword(blob: bytes, off: int) -> int:
    return int.from_bytes(blob[off : off + 4], "little")


def hash_stream(data: bytes) -> tuple[int, int]:
    eax = 0x811C9DC5
    last = 0
    for b in data:
        last = b ^ eax
        last = u32(last * 0x1000193)
        last = rol32(last, 5)
        eax = last ^ 0x7F4A7C15
    return eax, last


def decode_bytecode() -> bytes:
    a = read(0x402980, 0x3DF)
    b = read(0x4025A0, 0x3DF)
    return bytes(x ^ y for x, y in zip(a, b))


def run_vm() -> list[int]:
    code = decode_bytecode()
    regs = [0x13579BDF, 0x2468ACE1, 0x0F1E2D3C, 0x89ABCDEF]
    stack: list[int] = []
    mem = [0] * 256
    pc = 0
    key = 0x2D

    while pc <= 0x3DE:
        op = ((code[pc] ^ 0xA7) - key - 0x10) & 0xFF
        if op > 9:
            raise RuntimeError(f"bad opcode at {pc:#x}: {op:#x}")

        if op == 0:
            stack.append(regs[code[pc + 1] & 3])
            pc += 2
        elif op == 1:
            imm = int.from_bytes(code[pc + 1 : pc + 5], "little")
            stack.append(imm)
            pc += 5
        elif op == 2:
            b = stack.pop()
            stack[-1] = u32(stack[-1] ^ b)
            pc += 1
        elif op == 3:
            b = stack.pop()
            stack[-1] = u32(stack[-1] + b)
            pc += 1
        elif op == 4:
            imm = int.from_bytes(code[pc + 1 : pc + 5], "little")
            x = u32(stack[-1] ^ imm)
            x = u32(x - 0x61C88647)
            stack[-1] = rol32(x, (imm >> 27) + 1)
            pc += 5
        elif op == 5:
            stack[-1] = rol32(stack[-1], code[pc + 1])
            pc += 2
        elif op == 6:
            mem[code[pc + 1]] = stack[-1]
            pc += 2
        elif op == 7:
            regs[code[pc + 1] & 3] = stack.pop()
            pc += 2
        elif op == 8:
            key = code[pc + 1]
            pc += code[pc + 2] + 3
        elif op == 9:
            return mem

    raise RuntimeError("VM did not halt")


def generated_blocks(sel: int) -> tuple[bytes, bytes, bytes]:
    mem = run_vm()
    tab_key = [dword(read(0x402180, 16), i * 4) for i in range(4)]
    tab_main = read(0x4021A0, 4 * 33 * 4)
    tab_sub = read(0x4023C0, 33 * 4)
    tab_rot = read(0x402460, 33 * 4)
    tab_perm = read(0x402500, 33 * 4)

    out = bytearray()
    for i in range(33):
        idx = dword(tab_perm, i * 4)
        x = dword(tab_main, sel * 33 * 4 + i * 4)
        x ^= tab_key[sel]
        x ^= mem[idx]
        x = ror32(x, dword(tab_rot, i * 4))
        x = u32(x - dword(tab_sub, i * 4))
        out += x.to_bytes(4, "little")

    return bytes(out[:44]), bytes(out[44 : 44 + 44]), bytes(out[88 : 88 + 44])


def visited_indices() -> list[int]:
    out: list[int] = []

    def rec(r9: int, lo: int, hi: int) -> None:
        if r9 == 11:
            return
        while True:
            diff = hi - lo
            old = lo
            lo += diff // 2
            if diff > 8:
                rec(r9 + 1, old, lo)
            out.append(r9)
            if diff <= 8:
                return
            r9 += 1
            if r9 == 11:
                return

    r13 = 1
    lo = 0
    hi = 42
    while True:
        diff = hi - lo
        old = lo
        lo += diff // 2
        if diff > 8:
            rec(r13, old, lo)
        out.append(r13 - 1)
        if diff <= 8:
            return out
        r13 += 1


def simple(buf: bytes, seed: int) -> bytes:
    a = bytearray(buf)
    n = len(a)
    if n == 0:
        return bytes(a)

    rem = ((seed & 0xFF) | 1) % n
    cl = ((seed ^ 0xA5) + 0x13) & 0xFF
    cl ^= a[0]
    a[0] = cl
    k = read(0x402070, 8)
    for i in range(1, n):
        cl = (cl + k[i & 7]) & 0xFF
        cl ^= a[i]
        a[i] = cl

    r9 = seed + 0x0D
    for i in range(n):
        a[i] = (a[i] * (-59) + r9) & 0xFF
        r9 += 0x11

    step = rem
    if rem == 0:
        step = 1
    if n > 3 and step == 1:
        step = 3
    while gcd(step, n) != 1:
        step = (step + 2) % n
        if step <= 0:
            step += n

    off = (3 * (seed & 0xFF)) % n
    p = bytearray(n)
    for i, v in enumerate(a):
        p[(step * i + off) % n] = v
    a = p

    edi = seed + 7
    r12 = seed & 0xFF
    for _ in range(3):
        al = a[0] ^ (edi & 0xFF)
        a[0] = al
        if n > 1:
            c = (r12 + 1) & 7
            for i in range(1, n):
                al = rol8(al, c) ^ a[i]
                a[i] = al
        edi += 0x1D
        r12 = (r12 + 1) & 0xFF

    return bytes(a)


def inv_simple(buf: bytes, seed: int) -> bytes:
    a = bytearray(buf)
    n = len(a)
    if n == 0:
        return bytes(a)

    for round_no in reversed(range(3)):
        edi = seed + 7 + 0x1D * round_no
        r12 = (seed + round_no) & 0xFF
        c = (r12 + 1) & 7
        old = bytearray(n)
        prev = a[0]
        old[0] = prev ^ (edi & 0xFF)
        for i in range(1, n):
            old[i] = a[i] ^ rol8(prev, c)
            prev = a[i]
        a = old

    rem = ((seed & 0xFF) | 1) % n
    step = rem
    if rem == 0:
        step = 1
    if n > 3 and step == 1:
        step = 3
    while gcd(step, n) != 1:
        step = (step + 2) % n
        if step <= 0:
            step += n
    off = (3 * (seed & 0xFF)) % n
    old = bytearray(n)
    for i in range(n):
        old[i] = a[(step * i + off) % n]
    a = old

    inv_mul = pow((-59) & 0xFF, -1, 256)
    r9 = seed + 0x0D
    for i in range(n):
        a[i] = ((a[i] - r9) * inv_mul) & 0xFF
        r9 += 0x11

    k = read(0x402070, 8)
    prev = ((seed ^ 0xA5) + 0x13) & 0xFF
    old = bytearray(n)
    old[0] = a[0] ^ prev
    prev = a[0]
    for i in range(1, n):
        before = (prev + k[i & 7]) & 0xFF
        old[i] = a[i] ^ before
        prev = a[i]

    return bytes(old)


def transform(buf: bytes, rounds: int = 3, seed: int = 0x5D) -> bytes:
    if rounds == 0 or len(buf) <= 6:
        return simple(buf, seed)
    mid = len(buf) // 2
    left = transform(buf[:mid], rounds - 1, seed ^ 0x39)
    right = transform(buf[mid:], rounds - 1, seed ^ 0xC7)
    return simple(right + left, seed)


def inv_transform(buf: bytes, rounds: int = 3, seed: int = 0x5D) -> bytes:
    if rounds == 0 or len(buf) <= 6:
        return inv_simple(buf, seed)
    raw = inv_simple(buf, seed)
    mid = len(raw) // 2
    right_len = len(raw) - mid
    right = inv_transform(raw[:right_len], rounds - 1, seed ^ 0xC7)
    left = inv_transform(raw[right_len:], rounds - 1, seed ^ 0x39)
    return left + right


def crt_pair(a1: int, m1: int, a2: int, m2: int) -> tuple[int, int]:
    g = gcd(m1, m2)
    if (a2 - a1) % g:
        raise ValueError("inconsistent CRT")
    m1g, m2g = m1 // g, m2 // g
    t = ((a2 - a1) // g * pow(m1g, -1, m2g)) % m2g
    x = a1 + m1 * t
    mod = m1 * m2g
    return x % mod, mod


def crt(congruences: Iterable[tuple[int, int]]) -> tuple[int, int]:
    x, m = 0, 1
    for a, mod in congruences:
        x, m = crt_pair(x, m, a, mod)
    return x, m


def main() -> None:
    assert transform(inv_transform(bytes(range(42)))) == bytes(range(42))
    indices = sorted(set(visited_indices()))
    print("checked indices:", indices)
    print("visit order:", visited_indices())

    divs, resa, resb = generated_blocks(0)

    moduli4 = [dword(divs, i * 4) for i in range(4)]
    residues4 = [dword(resa, i * 4) for i in range(4)]
    x, mod = crt((residues4[i], moduli4[i]) for i in indices)
    loose = inv_transform(x.to_bytes(42, "big"))
    print(f"\nprogram only enforces first 4 constraints, one accepted binary input: {loose!r}")
    print(f"first-4 CRT modulus bits: {mod.bit_length()}")

    moduli11 = [dword(divs, i * 4) for i in range(11)]
    residues11 = [dword(resa, i * 4) for i in range(11)]
    x, mod = crt(zip(residues11, moduli11))
    flag = inv_transform(x.to_bytes(42, "big"))
    print(f"\nfull embedded table CRT modulus bits: {mod.bit_length()}")
    print(f"flag: {flag.decode()}")


if __name__ == "__main__":
    main()
