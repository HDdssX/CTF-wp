import ctypes
import struct
import sys
import time
from pathlib import Path


def build_ir():
    b = Path("main").read_bytes()[921:-4]
    maptok = {
        b"Dumb": ">",
        b"DumB": "<",
        b"dUmB": "+",
        b"dumb": "-",
        b"DUMB": ".",
        b"DUmB": ",",
        b"dUMb": "[",
        b"duMb": "]",
    }
    ir = []

    def emit(op, val=0):
        if op in ("add", "move"):
            if not val:
                return
            if ir and ir[-1][0] == op:
                nv = ir[-1][1] + val
                if nv:
                    ir[-1] = (op, nv)
                else:
                    ir.pop()
            else:
                ir.append((op, val))
        else:
            ir.append((op, val))

    for i in range(0, len(b), 4):
        c = maptok.get(b[i : i + 4])
        if c == ">":
            emit("move", 1)
        elif c == "<":
            emit("move", -1)
        elif c == "+":
            emit("add", 1)
        elif c == "-":
            emit("add", -1)
        elif c:
            emit(c, 0)
    return ir


def build_code(ir):
    code = bytearray()
    code += b"\x53\x57\x41\x54"  # push rbx; push rdi; push r12
    code += b"\x48\x89\xcb"  # mov rbx, rcx ; tape pointer
    code += b"\x48\x89\xd7"  # mov rdi, rdx ; callback pointer
    code += b"\x45\x31\xe4"  # xor r12d, r12d ; output count
    stack = []

    for op, val in ir:
        if op == "move":
            code += b"\x48\x81\xc3" + struct.pack("<i", val)
        elif op == "add":
            code += b"\x80\x03" + struct.pack("B", val & 0xFF)
        elif op == ".":
            code += b"\x0f\xb6\x0b"  # movzx ecx, byte [rbx]
            code += b"\x48\x83\xec\x20"  # shadow space
            code += b"\xff\xd7"  # call rdi
            code += b"\x48\x83\xc4\x20"
            code += b"\x49\xff\xc4"  # inc r12
        elif op == ",":
            code += b"\xc6\x03\x09"
        elif op == "[":
            start = len(code)
            code += b"\x80\x3b\x00"
            code += b"\x0f\x84\x00\x00\x00\x00"
            stack.append((start, len(code) - 4))
        elif op == "]":
            start, patchpos = stack.pop()
            code += b"\x80\x3b\x00"
            jne_pos = len(code)
            code += b"\x0f\x85\x00\x00\x00\x00"
            end = len(code)
            code[patchpos : patchpos + 4] = struct.pack("<i", end - (patchpos + 4))
            code[jne_pos + 2 : jne_pos + 6] = struct.pack("<i", start - (jne_pos + 6))

    if stack:
        raise RuntimeError("unbalanced brackets")
    code += b"\x4c\x89\xe0"  # mov rax, r12
    code += b"\x41\x5c\x5f\x5b\xc3"  # pop r12; pop rdi; pop rbx; ret
    return code


def main():
    ir = build_ir()
    print(f"ir={len(ir)}", flush=True)
    code = build_code(ir)
    print(f"code={len(code)}", flush=True)

    kernel32 = ctypes.windll.kernel32
    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    addr = kernel32.VirtualAlloc(None, len(code), 0x3000, 0x40)
    if not addr:
        raise OSError("VirtualAlloc failed")
    ctypes.memmove(addr, bytes(code), len(code))

    cap = 120_000_000
    tape = (ctypes.c_ubyte * cap)()
    start = time.time()
    output = bytearray()

    @ctypes.CFUNCTYPE(None, ctypes.c_uint32)
    def cb(byte):
        output.append(byte & 0xFF)
        sys.stdout.write(chr(byte & 0xFF))
        sys.stdout.flush()
        print(
            f"\n[output #{len(output)} byte=0x{byte & 0xff:02x} elapsed={time.time() - start:.2f}s]",
            file=sys.stderr,
            flush=True,
        )

    fn = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_void_p, ctypes.c_void_p)(addr)
    print("running", flush=True)
    n = fn(ctypes.cast(tape, ctypes.c_void_p), ctypes.cast(cb, ctypes.c_void_p))
    print(f"\ndone n={n} elapsed={time.time() - start:.2f}s repr={bytes(output)!r}", flush=True)


if __name__ == "__main__":
    main()
