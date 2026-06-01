import ctypes
import itertools
import multiprocessing as mp
import sys
import time

from wordfreq import top_n_list

TARGET = bytes.fromhex("4d3fc7f53b16754891ab67ed0622f4")
DLL_PATH = r"_extract\native\challenge_native.dll"
CHECK_RVA = 0x1390

LEET = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"})


def normalize_word(w):
    w = w.lower()
    if not w.isalpha():
        return None
    if len(w) < 2 or len(w) > 12:
        return None
    return w.translate(LEET)


def generate_candidates(limit=6000):
    raw = top_n_list("en", limit)
    words = []
    seen = set()
    for w in raw:
        v = normalize_word(w)
        if v and v not in seen:
            seen.add(v)
            words.append(v)

    by_len = {}
    for w in words:
        by_len.setdefault(len(w), []).append(w)

    yielded = set()

    def emit(p):
        if len(p) == 14:
            s = p + "}"
            if s not in yielded:
                yielded.add(s)
                yield s

    # One word.
    for w in by_len.get(14, []):
        yield from emit(w)

    # Two words.
    for l1 in range(2, 12):
        l2 = 13 - l1
        if l2 < 2:
            continue
        for a in by_len.get(l1, []):
            for b in by_len.get(l2, []):
                yield from emit(a + "_" + b)

    # Three words.
    for l1 in range(2, 11):
        for l2 in range(2, 11):
            l3 = 12 - l1 - l2
            if l3 < 2:
                continue
            for a in by_len.get(l1, []):
                for b in by_len.get(l2, []):
                    for c in by_len.get(l3, []):
                        yield from emit(a + "_" + b + "_" + c)

    # Deterministic variants of likely challenge/meme words not necessarily top-ranked.
    extras = [
        "not_down_again", "not_dead_again", "not_broken_lol", "not_cooked_lol",
        "not_on_fire", "no_more_down", "no_longer_down", "finally_stable",
        "stable_for_now", "working_again", "running_again", "up_and_running",
        "back_online", "back_up_again", "online_again", "alive_for_now",
        "fine_this_time", "fast_this_time", "fixed_for_once", "okay_this_time",
        "good_this_time", "ready_for_now", "healthy_again", "solid_for_now",
        "patched_again", "recovered_now", "restored_now",
    ]
    fillers = ["", "_", "!", "!!", "?", "??", "_0", "_1", "0", "1"]
    for p in extras:
        lp = p.translate(LEET)
        for f in fillers:
            yield from emit(lp + f)


def init_worker():
    global fn, envp, current, last_dest, callbacks
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
    kernel32.LoadLibraryW.restype = ctypes.c_void_p
    base = kernel32.LoadLibraryW(DLL_PATH)
    if not base:
        raise ctypes.WinError(ctypes.get_last_error())

    CALLBACK = ctypes.WINFUNCTYPE(
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
    callbacks = []
    table = (ctypes.c_void_p * 240)()
    current = b""
    last_dest = 0

    def make_cb(index):
        def cb(env, a1, a2, a3, a4, a5, a6, a7):
            global last_dest
            if index == 171:
                return 15
            if index in (200, 203):
                dest = int(a4 or 0)
                ctypes.memmove(dest, current, 15)
                last_dest = dest
                return 0
            return 0

        return CALLBACK(cb)

    for i in range(240):
        cb = make_cb(i)
        callbacks.append(cb)
        table[i] = ctypes.cast(cb, ctypes.c_void_p).value

    env = ctypes.c_void_p(ctypes.cast(table, ctypes.c_void_p).value)
    envp = ctypes.pointer(env)
    FUNC = ctypes.WINFUNCTYPE(ctypes.c_ubyte, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    fn = FUNC(base + CHECK_RVA)


def test_candidate(s):
    global current, last_dest
    current = s.encode("ascii")
    last_dest = 0
    res = fn(ctypes.cast(envp, ctypes.c_void_p), None, ctypes.c_void_p(0x1234))
    if res:
        return s
    out = ctypes.string_at(last_dest - 0x1E, 15)
    if out == TARGET:
        return s
    return None


def batched(iterable, n):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else min(16, mp.cpu_count())
    start = time.time()
    tested = 0
    with mp.Pool(workers, initializer=init_worker) as pool:
        for batch in batched(generate_candidates(limit), 2000):
            for hit in pool.imap_unordered(test_candidate, batch, chunksize=50):
                tested += 1
                if hit:
                    print("FOUND", hit, "tested", tested, "secs", time.time() - start, flush=True)
                    pool.terminate()
                    return
            if tested and tested % 100000 < 2000:
                print("progress", tested, "secs", round(time.time() - start, 1), flush=True)
    print("not found", tested, "secs", time.time() - start, flush=True)


if __name__ == "__main__":
    main()
