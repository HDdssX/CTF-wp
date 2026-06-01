import ctypes
import struct
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


def build_rle_ir():
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


def optimize_loop(body):
    if len(body) == 1 and body[0][0] == "move":
        return ("scan", body[0][1])

    ptr = 0
    effects = defaultdict(int)
    for node in body:
        op = node[0]
        if op == "move":
            ptr += node[1]
        elif op == "add":
            effects[ptr] += node[1]
        else:
            return ("loop", body)

    if ptr == 0:
        delta = effects.get(0, 0) & 0xFF
        if delta & 1:
            inv = pow(delta, -1, 256)
            mult = {off: coef & 0xFF for off, coef in effects.items() if off and (coef & 0xFF)}
            return ("mul", inv, mult)
    return ("loop", body)


def build_ast(ir):
    root = []
    stack = [root]
    max_depth = 0
    for op, val in ir:
        if op == "[":
            child = []
            stack[-1].append(("pending", child))
            stack.append(child)
            max_depth = max(max_depth, len(stack) - 1)
        elif op == "]":
            child = stack.pop()
            node = optimize_loop(child)
            parent = stack[-1]
            if not parent or parent[-1] != ("pending", child):
                raise RuntimeError("bad bracket stack")
            parent[-1] = node
        else:
            stack[-1].append((op, val))
    if len(stack) != 1:
        raise RuntimeError("unbalanced brackets")
    counts = Counter()

    def visit(body):
        for node in body:
            counts[node[0]] += 1
            if node[0] == "loop":
                visit(node[1])

    visit(root)
    return root, counts, max_depth


def rel32(code, patch_pos, target):
    code[patch_pos : patch_pos + 4] = struct.pack("<i", target - (patch_pos + 4))


def add_rbx_disp_cl(code, off):
    # add byte ptr [rbx+off], cl
    if off == 0:
        code += b"\x00\x0b"
    elif -128 <= off <= 127:
        code += b"\x00\x4b" + struct.pack("b", off)
    else:
        code += b"\x00\x8b" + struct.pack("<i", off)


def build_code(ast):
    code = bytearray()
    code += b"\x53\x57\x41\x54"  # push rbx; push rdi; push r12
    code += b"\x48\x89\xcb"  # mov rbx, rcx
    code += b"\x48\x89\xd7"  # mov rdi, rdx
    code += b"\x45\x31\xe4"  # xor r12d, r12d

    def emit_body(body):
        for node in body:
            op = node[0]
            if op == "move":
                code.extend(b"\x48\x81\xc3" + struct.pack("<i", node[1]))
            elif op == "add":
                code.extend(b"\x80\x03" + struct.pack("B", node[1] & 0xFF))
            elif op == ".":
                code.extend(b"\x0f\xb6\x0b")  # movzx ecx, byte [rbx]
                code.extend(b"\x48\x83\xec\x20")  # shadow space
                code.extend(b"\xff\xd7")  # call rdi
                code.extend(b"\x48\x83\xc4\x20")
                code.extend(b"\x49\xff\xc4")  # inc r12
            elif op == ",":
                code.extend(b"\xc6\x03\x09")  # VM input byte is main[4]
            elif op == "scan":
                start = len(code)
                code.extend(b"\x80\x3b\x00")  # cmp byte [rbx], 0
                code.extend(b"\x0f\x84\x00\x00\x00\x00")
                je_patch = len(code) - 4
                code.extend(b"\x48\x81\xc3" + struct.pack("<i", node[1]))
                code.extend(b"\xe9\x00\x00\x00\x00")
                jmp_patch = len(code) - 4
                end = len(code)
                rel32(code, je_patch, end)
                rel32(code, jmp_patch, start)
            elif op == "mul":
                inv, mult = node[1], node[2]
                code.extend(b"\x0f\xb6\x03")  # movzx eax, byte [rbx]
                code.extend(b"\x69\xc0" + struct.pack("<i", -inv))
                for off, coef in mult.items():
                    code.extend(b"\x89\xc1")  # mov ecx, eax
                    code.extend(b"\x69\xc9" + struct.pack("<i", coef))
                    add_rbx_disp_cl(code, off)
                code.extend(b"\xc6\x03\x00")  # clear source cell
            elif op == "loop":
                start = len(code)
                code.extend(b"\x80\x3b\x00")
                code.extend(b"\x0f\x84\x00\x00\x00\x00")
                je_patch = len(code) - 4
                emit_body(node[1])
                code.extend(b"\xe9\x00\x00\x00\x00")
                jmp_patch = len(code) - 4
                end = len(code)
                rel32(code, je_patch, end)
                rel32(code, jmp_patch, start)
            else:
                raise RuntimeError(op)

    emit_body(ast)
    code += b"\x4c\x89\xe0"  # mov rax, r12
    code += b"\x41\x5c\x5f\x5b\xc3"  # pop r12; pop rdi; pop rbx; ret
    return code


def main():
    started = time.time()
    ir = build_rle_ir()
    ast, counts, max_depth = build_ast(ir)
    print(f"ir={len(ir)} ast_counts={dict(counts)} max_depth={max_depth}", flush=True)
    code = build_code(ast)
    print(f"code={len(code)} build_elapsed={time.time() - started:.2f}s", flush=True)

    kernel32 = ctypes.windll.kernel32
    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    addr = kernel32.VirtualAlloc(None, len(code), 0x3000, 0x40)
    if not addr:
        raise OSError("VirtualAlloc failed")
    ctypes.memmove(addr, bytes(code), len(code))

    tape = (ctypes.c_ubyte * 120_000_000)()
    output = bytearray()
    run_started = time.time()

    @ctypes.CFUNCTYPE(None, ctypes.c_uint32)
    def cb(byte):
        byte &= 0xFF
        output.append(byte)
        sys.stdout.write(chr(byte))
        sys.stdout.flush()
        print(
            f"\n[output #{len(output)} byte=0x{byte:02x} elapsed={time.time() - run_started:.2f}s]",
            file=sys.stderr,
            flush=True,
        )

    fn = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_void_p, ctypes.c_void_p)(addr)
    print("running", flush=True)
    n = fn(ctypes.cast(tape, ctypes.c_void_p), ctypes.cast(cb, ctypes.c_void_p))
    print(f"\ndone n={n} elapsed={time.time() - run_started:.2f}s repr={bytes(output)!r}", flush=True)


if __name__ == "__main__":
    main()
