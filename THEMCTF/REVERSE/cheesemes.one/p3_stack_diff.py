import ctypes
import struct
import sys

DLL_PATH = r"_extract\native\challenge_native.dll"
CHECK_RVA = 0x1390

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
kernel32.LoadLibraryW.restype = ctypes.c_void_p
kernel32.VirtualQuery.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
kernel32.VirtualQuery.restype = ctypes.c_size_t


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("PartitionId", ctypes.c_ushort),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


base = kernel32.LoadLibraryW(DLL_PATH)
if not base:
    raise ctypes.WinError(ctypes.get_last_error())

CALLBACK = ctypes.WINFUNCTYPE(
    ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
)

callbacks = []
table_type = ctypes.c_void_p * 240
table = table_type()
last_region = None
current = b""


def readable(addr):
    mbi = MEMORY_BASIC_INFORMATION()
    if not kernel32.VirtualQuery(ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        return False
    if mbi.State != 0x1000:
        return False
    if mbi.Protect & (0x01 | 0x100):
        return False
    return True


def make_cb(index):
    def cb(env, a1, a2, a3, a4, a5, a6, a7):
        global last_region
        if index == 171:
            return len(current)
        if index in (184, 222):
            return 0
        if index in (192, 224):
            return 0
        if index in (200, 203):
            start = int(a2 or 0)
            n = int(a3 or 0)
            dest = int(a4 or 0)
            src = current[start:start + n]
            ctypes.memmove(dest, src, len(src))
            last_region = (dest, n)
            return 0
        return 0
    return CALLBACK(cb)


for i in range(len(table)):
    cb = make_cb(i)
    callbacks.append(cb)
    table[i] = ctypes.cast(cb, ctypes.c_void_p).value

env_value = ctypes.cast(table, ctypes.c_void_p).value
env = ctypes.c_void_p(env_value)
env_ptr = ctypes.pointer(env)
FUNC = ctypes.WINFUNCTYPE(ctypes.c_ubyte, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
fn = FUNC(base + CHECK_RVA)


def call_and_dump(s):
    global current, last_region
    current = s.encode()
    last_region = None
    res = fn(ctypes.cast(env_ptr, ctypes.c_void_p), None, ctypes.c_void_p(0x1234))
    if last_region is None:
        raise RuntimeError("no region")
    dest, n = last_region
    start = (dest - 0x28000) & ~0xfff
    end = (dest + 0x28000 + 0xfff) & ~0xfff
    chunks = {}
    for page in range(start, end, 0x1000):
        if readable(page):
            chunks[page - dest] = ctypes.string_at(page, 0x1000)
    return res, dest, chunks


a = sys.argv[1] if len(sys.argv) > 1 else "AAAAAAAAAAAAAAA"
b = sys.argv[2] if len(sys.argv) > 2 else "BBBBBBBBBBBBBBB"
ra, da, ca = call_and_dump(a)
rb, db, cb = call_and_dump(b)
print("res", ra, rb, "dest", hex(da), hex(db), "chunks", len(ca), len(cb))
diffs = []
for rel in sorted(set(ca) & set(cb)):
    ba = ca[rel]
    bb = cb[rel]
    for i, (x, y) in enumerate(zip(ba, bb)):
        if x != y:
            diffs.append((rel + i, x, y))
print("diff-count", len(diffs))
for off, x, y in diffs[:300]:
    print(f"{off:+#x}: {x:02x}->{y:02x}")
