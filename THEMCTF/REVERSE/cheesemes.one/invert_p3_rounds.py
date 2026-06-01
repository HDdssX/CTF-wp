import ctypes

DLL_PATH = r"_extract\native\challenge_native.dll"
CHECK_RVA = 0x1390
TARGET = bytes.fromhex("4d3fc7f53b16754891ab67ed0622f4")

STORE_STARTS = [
    0xB9780,
    0xB9A25,
    0xB9C7C,
    0xB9F29,
    0xBA116,
    0xBA3C7,
    0xBA5B4,
    0xBA861,
    0xBAA4E,
    0xBACFF,
    0xBAEF8,
]

NOOP4 = bytes.fromhex("4a0e7474")  # VM mov r0, r0; same length as the store op.


class NativeRoundOracle:
    def __init__(self):
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
        self.kernel32.LoadLibraryW.restype = ctypes.c_void_p
        self.kernel32.VirtualProtect.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
        ]
        self.kernel32.VirtualProtect.restype = ctypes.c_int

        self.base = self.kernel32.LoadLibraryW(DLL_PATH)
        if not self.base:
            raise ctypes.WinError(ctypes.get_last_error())

        self.original = {
            rva: ctypes.string_at(self.base + rva, 4)
            for rva in STORE_STARTS
        }
        self.current_round = None
        self.current = b"\0" * 15
        self.prefill = None
        self.last_dest = 0

        callback = ctypes.WINFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )
        self.callbacks = []
        table = (ctypes.c_void_p * 240)()

        def make_cb(index):
            def cb(env, a1, a2, a3, a4, a5, a6, a7):
                if index == 171:
                    return 15
                if index in (200, 203):
                    dest = int(a4 or 0)
                    ctypes.memmove(dest, self.current, 15)
                    if self.prefill is not None:
                        ctypes.memmove(dest - 0x1E, self.prefill, 15)
                    self.last_dest = dest
                    return 0
                return 0

            return callback(cb)

        for i in range(240):
            cb = make_cb(i)
            self.callbacks.append(cb)
            table[i] = ctypes.cast(cb, ctypes.c_void_p).value

        env = ctypes.c_void_p(ctypes.cast(table, ctypes.c_void_p).value)
        self.envp = ctypes.pointer(env)
        func = ctypes.WINFUNCTYPE(ctypes.c_ubyte, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
        self.fn = func(self.base + CHECK_RVA)

    def patch(self, rva, data):
        addr = self.base + rva
        old = ctypes.c_ulong()
        self.kernel32.VirtualProtect(addr, len(data), 0x40, ctypes.byref(old))
        ctypes.memmove(addr, data, len(data))
        restore = ctypes.c_ulong()
        self.kernel32.VirtualProtect(addr, len(data), old.value, ctypes.byref(restore))

    def set_round(self, round_index):
        if self.current_round == round_index:
            return
        for rva, data in self.original.items():
            self.patch(rva, data)
        for rva in STORE_STARTS[:round_index]:
            self.patch(rva, NOOP4)
        if round_index < 10:
            self.patch(STORE_STARTS[round_index + 1], b"\xAC")
        self.current_round = round_index

    def query(self, round_index, state_or_input):
        self.set_round(round_index)
        if round_index == 0:
            self.current = bytes(state_or_input)
            self.prefill = None
        else:
            self.current = b"\0" * 15
            self.prefill = bytes(state_or_input)
        self.last_dest = 0
        self.fn(ctypes.cast(self.envp, ctypes.c_void_p), None, ctypes.c_void_p(0x1234))
        return bytes(ctypes.string_at(self.last_dest - 0x1E, 15))


def invert_round(oracle, round_index, target):
    ascending = round_index % 2 == 1
    state = [0] * 15
    order = range(15) if ascending else range(14, -1, -1)
    for pos in order:
        matches = []
        for cand in range(256):
            state[pos] = cand
            out = oracle.query(round_index, state)
            if out[pos] != target[pos]:
                continue
            if ascending and out[:pos] != target[:pos]:
                continue
            if not ascending and out[pos + 1:] != target[pos + 1:]:
                continue
            matches.append(cand)
        if len(matches) != 1:
            raise RuntimeError(
                f"round {round_index} pos {pos} had {len(matches)} matches: {matches[:8]}"
            )
        state[pos] = matches[0]
    return bytes(state)


def invert_round0(oracle, target):
    plain = [0] * 15
    for pos in range(15):
        matches = []
        probe = bytearray(15)
        for cand in range(256):
            probe[pos] = cand
            out = oracle.query(0, probe)
            if out[pos] == target[pos]:
                matches.append(cand)
        if len(matches) != 1:
            raise RuntimeError(f"round 0 pos {pos} had {len(matches)} matches")
        plain[pos] = matches[0]
        probe[pos] = 0
    return bytes(plain)


def main():
    oracle = NativeRoundOracle()
    state = TARGET
    print("target", state.hex(), flush=True)
    for round_index in range(10, 0, -1):
        state = invert_round(oracle, round_index, state)
        print(f"before round {round_index}:", state.hex(), flush=True)
    plain = invert_round0(oracle, state)
    print("plain-bytes", plain.hex(), flush=True)
    print("plain-ascii", plain.decode("latin1"), flush=True)
    final = oracle.query(10, oracle.query(9, oracle.query(8, oracle.query(7, oracle.query(6, oracle.query(5, oracle.query(4, oracle.query(3, oracle.query(2, oracle.query(1, oracle.query(0, plain)))))))))))
    print("recomputed", final.hex(), flush=True)


if __name__ == "__main__":
    main()
