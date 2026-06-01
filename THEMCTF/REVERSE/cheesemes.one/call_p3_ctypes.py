import ctypes
import sys

DLL_PATH = r"_extract\native\challenge_native.dll"
BASE_RVA_CHECK = 0x1390

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
kernel32.LoadLibraryW.restype = ctypes.c_void_p
kernel32.VirtualProtect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
kernel32.VirtualProtect.restype = ctypes.c_int
kernel32.AddVectoredExceptionHandler.argtypes = [ctypes.c_ulong, ctypes.c_void_p]
kernel32.AddVectoredExceptionHandler.restype = ctypes.c_void_p

base = kernel32.LoadLibraryW(DLL_PATH)
if not base:
    raise ctypes.WinError(ctypes.get_last_error())

candidate = (sys.argv[1] if len(sys.argv) > 1 else "A" * 15).encode()
buf = (ctypes.c_byte * max(1, len(candidate)))()
for i, b in enumerate(candidate):
    buf[i] = b if b < 128 else b - 256

CALLBACK = ctypes.WINFUNCTYPE(
    ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
)

callbacks = []
regions = []
guard_enabled = "--guard" in sys.argv

PAGE_READWRITE = 0x04
PAGE_GUARD = 0x100
EXCEPTION_CONTINUE_EXECUTION = -1
EXCEPTION_CONTINUE_SEARCH = 0
STATUS_GUARD_PAGE_VIOLATION = 0x80000001
STATUS_SINGLE_STEP = 0x80000004
guard_page = 0
guard_target_lo = 0
guard_target_hi = 0
guard_hits = 0


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [
    ("ExceptionCode", ctypes.c_uint32),
    ("ExceptionFlags", ctypes.c_uint32),
    ("ExceptionRecord", ctypes.POINTER(EXCEPTION_RECORD)),
    ("ExceptionAddress", ctypes.c_void_p),
    ("NumberParameters", ctypes.c_uint32),
    ("ExceptionInformation", ctypes.c_uint64 * 15),
]


class EXCEPTION_POINTERS(ctypes.Structure):
    _fields_ = [("ExceptionRecord", ctypes.POINTER(EXCEPTION_RECORD)), ("ContextRecord", ctypes.c_void_p)]


VEH = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.POINTER(EXCEPTION_POINTERS))


@VEH
def veh_handler(info):
    global guard_hits
    rec = info.contents.ExceptionRecord.contents
    if rec.ExceptionCode == STATUS_GUARD_PAGE_VIOLATION:
        access = rec.ExceptionInformation[1]
        guard_hits += 1
        if guard_hits <= 80 or (guard_target_lo <= access < guard_target_hi):
            print("guard", guard_hits, "pc=" + hex(rec.ExceptionAddress or 0), "access=" + hex(access), "kind=" + hex(rec.ExceptionInformation[0]), flush=True)
        ctx = int(info.contents.ContextRecord or 0)
        if ctx:
            eflags = ctypes.c_uint32.from_address(ctx + 0x44)
            eflags.value |= 0x100
        return EXCEPTION_CONTINUE_EXECUTION
    if rec.ExceptionCode == STATUS_SINGLE_STEP and guard_page:
        old = ctypes.c_ulong()
        kernel32.VirtualProtect(ctypes.c_void_p(guard_page), ctypes.c_size_t(0x1000), PAGE_READWRITE | PAGE_GUARD, ctypes.byref(old))
        return EXCEPTION_CONTINUE_EXECUTION
    return EXCEPTION_CONTINUE_SEARCH


if guard_enabled:
    kernel32.AddVectoredExceptionHandler(1, ctypes.cast(veh_handler, ctypes.c_void_p))

def make_cb(index):
    def cb(env, a1, a2, a3, a4, a5, a6, a7):
        # Common JNI byte-array operations. Return values are pointer-sized;
        # integer return values are accepted in the low bits by the caller.
        if index in (171,):  # GetArrayLength
            return len(candidate)
        if index in (184, 222):  # GetByteArrayElements / GetPrimitiveArrayCritical
            return ctypes.addressof(buf)
        if index in (192, 224):  # ReleaseByteArrayElements / ReleasePrimitiveArrayCritical
            return 0
        if index in (200, 203):  # GetByteArrayRegion(env, array, start, len, buf)
            start = int(a2 or 0)
            n = int(a3 or 0)
            dest = int(a4 or 0)
            regions.append((dest, n))
            ctypes.memmove(dest, ctypes.addressof(buf) + start, n)
            if guard_enabled:
                global_guard = globals()
                old = ctypes.c_ulong()
                page = dest & ~0xfff
                global_guard["guard_page"] = page
                global_guard["guard_target_lo"] = dest - 0x40
                global_guard["guard_target_hi"] = dest + 0x40
                global_guard["guard_hits"] = 0
                ok = kernel32.VirtualProtect(ctypes.c_void_p(page), ctypes.c_size_t(0x1000), PAGE_READWRITE | PAGE_GUARD, ctypes.byref(old))
                print("guard-set", hex(page), ok, hex(old.value), "err", ctypes.get_last_error(), flush=True)
            return 0
        def hx(value):
            return "0" if value is None else f"{int(value):x}"
        print(f"jni[{index}] env={hx(env)} a1={hx(a1)} a2={hx(a2)} a3={hx(a3)} a4={hx(a4)}", flush=True)
        return 0
    return CALLBACK(cb)

table_type = ctypes.c_void_p * 240
table = table_type()
for i in range(len(table)):
    cb = make_cb(i)
    callbacks.append(cb)
    table[i] = ctypes.cast(cb, ctypes.c_void_p).value

env_value = ctypes.cast(table, ctypes.c_void_p).value
env = ctypes.c_void_p(env_value)
env_ptr = ctypes.pointer(env)

FUNC = ctypes.WINFUNCTYPE(ctypes.c_ubyte, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
fn = FUNC(base + BASE_RVA_CHECK)
res = fn(ctypes.cast(env_ptr, ctypes.c_void_p), None, ctypes.c_void_p(0x1234))
print("result", res)
for dest, n in regions:
    raw = ctypes.string_at(dest, min(128, max(n, 64)))
    print("region", hex(dest), raw.hex())
