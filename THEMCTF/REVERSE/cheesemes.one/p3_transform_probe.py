import ctypes
import sys

DLL_PATH = r"_extract\native\challenge_native.dll"
CHECK_RVA = 0x1390

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
kernel32.LoadLibraryW.restype = ctypes.c_void_p
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
current = b""
last_dest = 0


def make_cb(index):
    def cb(env, a1, a2, a3, a4, a5, a6, a7):
        global last_dest
        if index == 171:
            return len(current)
        if index in (200, 203):
            start = int(a2 or 0)
            n = int(a3 or 0)
            dest = int(a4 or 0)
            ctypes.memmove(dest, current[start:start + n], n)
            last_dest = dest
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


def run(s):
    global current, last_dest
    current = s.encode()
    last_dest = 0
    res = fn(ctypes.cast(env_ptr, ctypes.c_void_p), None, ctypes.c_void_p(0x1234))
    out = ctypes.string_at(last_dest - 0x1e, 15)
    return res, out


for arg in (sys.argv[1:] or ["AAAAAAAAAAAAAAA", "BBBBBBBBBBBBBBB"]):
    res, out = run(arg)
    print(arg, res, out.hex())
