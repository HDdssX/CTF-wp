import ctypes
import struct
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

TRACE_PCS = {
    199,
    1355,
    1024960,
    1085906,
    1091930,
    1091998,
    1092010,
    1092129,
    1092256,
    1092501,
    1092872,
    1092938,
    1093021,
    1093218,
    1093463,
    1093900,
    1093906,
    1093918,
    1093973,
    1094007,
    1094013,
    1094047,
    1094053,
    1094087,
    1094116,
    1097716,
    1113992,
    1126419,
}


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
        pc = len(ir)
        if op in ("add", "move"):
            if not val:
                return
            if ir and ir[-1][0] == op:
                old_op, old_val, old_pc = ir[-1]
                nv = old_val + val
                if nv:
                    ir[-1] = (old_op, nv, old_pc)
                else:
                    ir.pop()
            else:
                ir.append((op, val, pc))
        else:
            ir.append((op, val, pc))

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
    # Reassign pc after RLE cancellations so it matches final IR indices.
    return [(op, val, i) for i, (op, val, _pc) in enumerate(ir)]


def optimize_loop(start_pc, body):
    if len(body) == 1 and body[0][0] == "move":
        return ("scan", start_pc, body[0][2])
    ptr = 0
    effects = defaultdict(int)
    for node in body:
        op = node[0]
        if op == "move":
            ptr += node[2]
        elif op == "add":
            effects[ptr] += node[2]
        else:
            return ("loop", start_pc, body)
    if ptr == 0:
        delta = effects.get(0, 0) & 0xFF
        if delta & 1:
            inv = pow(delta, -1, 256)
            mult = {off: coef & 0xFF for off, coef in effects.items() if off and (coef & 0xFF)}
            return ("mul", start_pc, inv, mult)
    return ("loop", start_pc, body)


def build_ast(ir):
    root = []
    stack = [root]
    start_pcs = []
    for op, val, pc in ir:
        if op == "[":
            child = []
            stack[-1].append(("pending", pc, child))
            stack.append(child)
            start_pcs.append(pc)
        elif op == "]":
            child = stack.pop()
            start_pc = start_pcs.pop()
            node = optimize_loop(start_pc, child)
            stack[-1][-1] = node
        else:
            stack[-1].append((op, pc, val))
    counts = Counter()

    def visit(body):
        for node in body:
            counts[node[0]] += 1
            if node[0] == "loop":
                visit(node[2])

    visit(root)
    return root, counts


def rel32(code, patch_pos, target):
    code[patch_pos : patch_pos + 4] = struct.pack("<i", target - (patch_pos + 4))


def add_rbx_disp_cl(code, off):
    if off == 0:
        code += b"\x00\x0b"
    elif -128 <= off <= 127:
        code += b"\x00\x4b" + struct.pack("b", off)
    else:
        code += b"\x00\x8b" + struct.pack("<i", off)


def emit_trace(code, pc):
    if pc not in TRACE_PCS:
        return
    code.extend(b"\xb9" + struct.pack("<I", pc))  # mov ecx, pc
    code.extend(b"\x48\x89\xda")  # mov rdx, rbx
    code.extend(b"\x4c\x29\xf2")  # sub rdx, r14
    code.extend(b"\x0f\xb6\x03")  # movzx eax, byte [rbx]
    code.extend(b"\x41\x89\xc0")  # mov r8d, eax
    code.extend(b"\x48\x83\xec\x20")
    code.extend(b"\x41\xff\xd5")  # call r13
    code.extend(b"\x48\x83\xc4\x20")


def build_code(ast):
    code = bytearray()
    code += b"\x53\x57\x41\x54\x41\x55\x41\x56"  # rbx,rdi,r12,r13,r14
    code += b"\x48\x89\xcb"  # mov rbx, rcx
    code += b"\x49\x89\xce"  # mov r14, rcx
    code += b"\x48\x89\xd7"  # mov rdi, rdx
    code += b"\x4d\x89\xc5"  # mov r13, r8
    code += b"\x45\x31\xe4"  # xor r12d, r12d

    def emit_body(body):
        for node in body:
            op = node[0]
            pc = node[1]
            if op == "move":
                code.extend(b"\x48\x81\xc3" + struct.pack("<i", node[2]))
            elif op == "add":
                code.extend(b"\x80\x03" + struct.pack("B", node[2] & 0xFF))
            elif op == ".":
                code.extend(b"\x0f\xb6\x0b")
                code.extend(b"\x48\x83\xec\x20")
                code.extend(b"\xff\xd7")
                code.extend(b"\x48\x83\xc4\x20")
                code.extend(b"\x49\xff\xc4")
            elif op == ",":
                code.extend(b"\xc6\x03\x09")
            elif op == "scan":
                emit_trace(code, pc)
                start = len(code)
                code.extend(b"\x80\x3b\x00")
                code.extend(b"\x0f\x84\x00\x00\x00\x00")
                je_patch = len(code) - 4
                code.extend(b"\x48\x81\xc3" + struct.pack("<i", node[2]))
                code.extend(b"\xe9\x00\x00\x00\x00")
                jmp_patch = len(code) - 4
                end = len(code)
                rel32(code, je_patch, end)
                rel32(code, jmp_patch, start)
            elif op == "mul":
                emit_trace(code, pc)
                inv, mult = node[2], node[3]
                code.extend(b"\x0f\xb6\x03")
                code.extend(b"\x69\xc0" + struct.pack("<i", -inv))
                for off, coef in mult.items():
                    code.extend(b"\x89\xc1")
                    code.extend(b"\x69\xc9" + struct.pack("<i", coef))
                    add_rbx_disp_cl(code, off)
                code.extend(b"\xc6\x03\x00")
            elif op == "loop":
                start = len(code)
                code.extend(b"\x80\x3b\x00")
                code.extend(b"\x0f\x84\x00\x00\x00\x00")
                je_patch = len(code) - 4
                emit_trace(code, pc)
                emit_body(node[2])
                code.extend(b"\xe9\x00\x00\x00\x00")
                jmp_patch = len(code) - 4
                end = len(code)
                rel32(code, je_patch, end)
                rel32(code, jmp_patch, start)

    emit_body(ast)
    code += b"\x4c\x89\xe0"
    code += b"\x41\x5e\x41\x5d\x41\x5c\x5f\x5b\xc3"
    return code


def main():
    ir = build_rle_ir()
    ast, counts = build_ast(ir)
    print(f"ir={len(ir)} counts={dict(counts)}", flush=True)
    code = build_code(ast)
    print(f"code={len(code)}", flush=True)
    kernel32 = ctypes.windll.kernel32
    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    addr = kernel32.VirtualAlloc(None, len(code), 0x3000, 0x40)
    ctypes.memmove(addr, bytes(code), len(code))
    tape = (ctypes.c_ubyte * 120_000_000)()
    started = time.time()
    output = bytearray()
    trace_counts = Counter()

    @ctypes.CFUNCTYPE(None, ctypes.c_uint32)
    def out_cb(byte):
        output.append(byte & 0xFF)
        sys.stdout.write(chr(byte & 0xFF))
        sys.stdout.flush()
        print(f"\nOUT#{len(output)} byte={byte & 0xff:02x} elapsed={time.time()-started:.2f}", file=sys.stderr, flush=True)

    @ctypes.CFUNCTYPE(None, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint32)
    def trace_cb(pc, ptr, val):
        trace_counts[pc] += 1
        n = trace_counts[pc]
        if n <= 20 or n in (50, 100, 200, 500, 1000, 2000, 5000, 10000):
            print(f"TRACE pc={pc} n={n} ptr={ptr} val={val & 0xff} elapsed={time.time()-started:.2f}", file=sys.stderr, flush=True)

    fn = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(addr)
    print("running", flush=True)
    n = fn(ctypes.cast(tape, ctypes.c_void_p), ctypes.cast(out_cb, ctypes.c_void_p), ctypes.cast(trace_cb, ctypes.c_void_p))
    print(f"\ndone n={n} repr={bytes(output)!r}", flush=True)


if __name__ == "__main__":
    main()
