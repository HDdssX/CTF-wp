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

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
kernel32.LoadLibraryW.restype = ctypes.c_void_p

pe = pefile.PE(PATH)
loaded_base = kernel32.LoadLibraryW(PATH)
if not loaded_base:
    raise ctypes.WinError(ctypes.get_last_error())


def map_region(mu, addr, size, perms=7):
    addr &= ~0xFFF
    size = (size + 0xFFF) & ~0xFFF
    mu.mem_map(addr, size, perms)


def write_u64(mu, addr, value):
    mu.mem_write(addr, struct.pack("<Q", value & ((1 << 64) - 1)))


def read_u64(mu, addr):
    return struct.unpack("<Q", mu.mem_read(addr, 8))[0]


def map_runtime_image(mu):
    image_size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
    map_region(mu, loaded_base, image_size)
    headers = ctypes.string_at(loaded_base, pe.OPTIONAL_HEADER.SizeOfHeaders)
    mu.mem_write(loaded_base, headers)
    for sec in pe.sections:
        size = max(sec.Misc_VirtualSize, sec.SizeOfRawData)
        data = ctypes.string_at(loaded_base + sec.VirtualAddress, size)
        mu.mem_write(loaded_base + sec.VirtualAddress, data)


def run(candidate: bytes, trace=False, trace_vm=False, hook_setup=None):
    mu = Uc(UC_ARCH_X86, UC_MODE_64)
    map_region(mu, 0, 0x10000)
    map_runtime_image(mu)

    map_region(mu, STUB_BASE, 0x10000)
    for i in range(0, 0x10000, 0x10):
        mu.mem_write(STUB_BASE + i, b"\xC3")

    map_region(mu, ENV_BASE, 0x20000)
    table_addr = ENV_BASE + 0x1000
    env_ptr = ENV_BASE + 0x800
    write_u64(mu, env_ptr, table_addr)
    for i in range(240):
        write_u64(mu, table_addr + i * 8, STUB_BASE + i * 0x10)

    input_addr = ENV_BASE + 0x8000
    mu.mem_write(input_addr, candidate)

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
    state = {"last_dest": None, "regions": regions}

    def hook_code(mu, address, size, user_data):
        if address == RET_SENTINEL:
            mu.emu_stop()
            return
        if STUB_BASE <= address < STUB_BASE + 0x10000:
            idx = (address - STUB_BASE) // 0x10
            cur_rsp = mu.reg_read(UC_X86_REG_RSP)
            if idx == 171:
                mu.reg_write(UC_X86_REG_RAX, len(candidate))
            elif idx in (184, 222):
                mu.reg_write(UC_X86_REG_RAX, input_addr)
            elif idx in (192, 224):
                mu.reg_write(UC_X86_REG_RAX, 0)
            elif idx in (200, 203):
                start = mu.reg_read(UC_X86_REG_R8)
                n = mu.reg_read(UC_X86_REG_R9)
                dest = read_u64(mu, cur_rsp + 0x28)
                if trace:
                    print("GetByteArrayRegion", hex(dest), start, n, "rsp", hex(cur_rsp))
                mu.mem_write(dest, candidate[start:start + n])
                regions.append((dest, n))
                state["last_dest"] = dest
                mu.reg_write(UC_X86_REG_RAX, 0)
            else:
                calls.append(idx)
                if trace:
                    print(
                        "jni",
                        idx,
                        hex(mu.reg_read(UC_X86_REG_RCX)),
                        hex(mu.reg_read(UC_X86_REG_RDX)),
                        hex(mu.reg_read(UC_X86_REG_R8)),
                        hex(mu.reg_read(UC_X86_REG_R9)),
                    )
                mu.reg_write(UC_X86_REG_RAX, 0)
        elif trace_vm and address == loaded_base + 0x20087:
            rsi = mu.reg_read(UC_X86_REG_RSI)
            try:
                op = mu.mem_read(rsi, 1)[0]
            except Exception:
                op = None
            print("vm", hex(rsi - loaded_base), "op", "??" if op is None else hex(op))

    def invalid(mu, access, address, size, value, user_data):
        if trace:
            print(
                "invalid",
                access,
                hex(address),
                size,
                "rip",
                hex(mu.reg_read(UC_X86_REG_RIP) - loaded_base),
            )
        return False

    mu.hook_add(UC_HOOK_CODE, hook_code)
    mu.hook_add(UC_HOOK_MEM_INVALID, invalid)
    if hook_setup is not None:
        hook_setup(mu, state)
    mu.emu_start(loaded_base + CHECK_RVA, RET_SENTINEL, timeout=0, count=100_000_000)
    return mu, mu.reg_read(UC_X86_REG_RAX) & 0xFF, calls, regions


if __name__ == "__main__":
    s = (sys.argv[1] if len(sys.argv) > 1 else "A" * 15).encode()
    mu, result, calls, regions = run(s, trace="--trace" in sys.argv, trace_vm="--trace-vm" in sys.argv)
    print("base", hex(loaded_base))
    print("result", result, "calls", calls, "regions", [(hex(a), n) for a, n in regions])
    for dest, n in regions:
        print("region", hex(dest), mu.mem_read(dest, min(128, max(n, 64))).hex())
        print("derived", mu.mem_read(dest - 0x1E, 15).hex())
