import ctypes
import struct
import sys

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE, UC_HOOK_MEM_INVALID
from unicorn.x86_const import *

PATH = r"_extract\native\challenge_native.dll"
CHECK_RVA = 0x1390
RET_SENTINEL = 0x4141414141414141
STUB_BASE = 0x100000000
ENV_BASE = 0x100100000
STACK_BASE = 0x100200000
STACK_SIZE = 0x800000

pe = pefile.PE(PATH)
base = pe.OPTIONAL_HEADER.ImageBase
image_size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
raw = open(PATH, "rb").read()


def map_region(mu, addr, size, perms=7):
    addr &= ~0xfff
    size = (size + 0xfff) & ~0xfff
    mu.mem_map(addr, size, perms)


def write(mu, addr, data):
    mu.mem_write(addr, data)


def read_u64(mu, addr):
    return struct.unpack("<Q", mu.mem_read(addr, 8))[0]


def write_u64(mu, addr, value):
    mu.mem_write(addr, struct.pack("<Q", value & ((1 << 64) - 1)))


def run(candidate: bytes, trace=False):
    mu = Uc(UC_ARCH_X86, UC_MODE_64)
    map_region(mu, 0, 0x10000)
    map_region(mu, base, image_size)
    # Headers help code that walks its own PE image.
    write(mu, base, raw[: pe.OPTIONAL_HEADER.SizeOfHeaders])
    for sec in pe.sections:
        data = sec.get_data()
        write(mu, base + sec.VirtualAddress, data)

    map_region(mu, STUB_BASE, 0x10000)
    for i in range(0, 0x10000, 0x10):
        write(mu, STUB_BASE + i, b"\xc3")  # ret

    map_region(mu, ENV_BASE, 0x20000)
    table_addr = ENV_BASE + 0x1000
    env_ptr = ENV_BASE + 0x800
    write_u64(mu, env_ptr, table_addr)
    for i in range(240):
        write_u64(mu, table_addr + i * 8, STUB_BASE + i * 0x10)

    input_addr = ENV_BASE + 0x8000
    write(mu, input_addr, candidate)

    map_region(mu, STACK_BASE, STACK_SIZE)
    rsp = STACK_BASE + STACK_SIZE - 0x1000
    write_u64(mu, rsp, RET_SENTINEL)
    mu.reg_write(UC_X86_REG_RSP, rsp)
    mu.reg_write(UC_X86_REG_RCX, env_ptr)
    mu.reg_write(UC_X86_REG_RDX, 0)
    mu.reg_write(UC_X86_REG_R8, 0x1234)
    mu.reg_write(UC_X86_REG_R9, 0)

    calls = []
    regions = []

    def hook_code(mu, address, size, user_data):
        if address == RET_SENTINEL:
            mu.emu_stop()
            return
        if STUB_BASE <= address < STUB_BASE + 0x10000:
            idx = (address - STUB_BASE) // 0x10
            cur_rsp = mu.reg_read(UC_X86_REG_RSP)
            if idx == 171:  # GetArrayLength
                mu.reg_write(UC_X86_REG_RAX, len(candidate))
            elif idx in (184, 222):  # GetByteArrayElements / GetPrimitiveArrayCritical
                mu.reg_write(UC_X86_REG_RAX, input_addr)
            elif idx in (192, 224):  # releases
                mu.reg_write(UC_X86_REG_RAX, 0)
            elif idx in (200, 203):  # GetByteArrayRegion
                start = mu.reg_read(UC_X86_REG_R8)
                n = mu.reg_read(UC_X86_REG_R9)
                dest = read_u64(mu, cur_rsp + 0x28)
                if trace:
                    print("GetByteArrayRegion", hex(dest), start, n, "rsp", hex(cur_rsp))
                write(mu, dest, candidate[start:start + n])
                regions.append((dest, n))
                mu.reg_write(UC_X86_REG_RAX, 0)
            else:
                calls.append(idx)
                if trace:
                    print("jni", idx, hex(mu.reg_read(UC_X86_REG_RCX)), hex(mu.reg_read(UC_X86_REG_RDX)),
                          hex(mu.reg_read(UC_X86_REG_R8)), hex(mu.reg_read(UC_X86_REG_R9)))
                mu.reg_write(UC_X86_REG_RAX, 0)
        elif trace and (address & 0xfff) == 0:
            print("pc", hex(address - base))

    def invalid(mu, access, address, size, value, user_data):
        if trace:
            print("invalid", access, hex(address), size, "rip", hex(mu.reg_read(UC_X86_REG_RIP) - base))
        try:
            map_region(mu, address, 0x1000)
            return True
        except Exception:
            return False

    mu.hook_add(UC_HOOK_CODE, hook_code)
    mu.hook_add(UC_HOOK_MEM_INVALID, invalid)
    try:
        mu.emu_start(base + CHECK_RVA, RET_SENTINEL, timeout=0, count=50_000_000)
    except Exception as e:
        print("emu error", e, "rip", hex(mu.reg_read(UC_X86_REG_RIP) - base))
        raise
    return mu.reg_read(UC_X86_REG_RAX) & 0xff, calls, regions


if __name__ == "__main__":
    s = (sys.argv[1] if len(sys.argv) > 1 else "A" * 15).encode()
    result, calls, regions = run(s, trace="--trace" in sys.argv)
    print("result", result, "calls", calls, "regions", [(hex(a), n) for a, n in regions])
