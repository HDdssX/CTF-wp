from pathlib import Path
import re, zlib, gzip, bz2, lzma

# 读你现在这串可见字符（就是 base100 解出来的那段）
s = r"""I2,2m&WS3Ref1kYdMa7yV$nTuL0\#WO^VQieJQtC+UKV"0eIN%|R*%f,<>/$3>AS.7?0CfPrSZwNO;_=Eav!0lQC%TDLh1f.GVa~z:I9OGZ:U>wY/~>!@.3t3+6^W)R+H8p5d6RZ^WObkM:4z;5^*Z!Y.k7ifFBdK!(=d"IhHg7begz7aDyzdD$,4eZFf+z(F_7&ukKK;,v[VO?zFnqvzV6Q^)k[i:/`cPY(B[J.@:ObkDSo/.yio)9YY7C<hqi.ZUYnd2$<_t[OiI)C"""

FLAG_RE = re.compile(rb"hgame\{[^}]{1,200}\}")

B91_TABLE = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    "!#$%&()*+,./:;<=>?@[]^_`{|}~\"\\"
)
# 上面这串长度必须是 91
# assert len(B91_TABLE) == 91
DEC = {ord(c): i for i, c in enumerate(B91_TABLE)}

def base91_decode(data: str) -> bytes:
    v = -1
    b = 0
    n = 0
    out = bytearray()
    for ch in data:
        o = ord(ch)
        if o not in DEC:
            # 跳过换行/空白
            if ch.isspace():
                continue
            raise ValueError(f"invalid base91 char: {ch!r} (U+{o:04X})")
        c = DEC[o]
        if v < 0:
            v = c
        else:
            v += c * 91
            b |= v << n
            n += 13 if (v & 8191) > 88 else 14
            while n >= 8:
                out.append(b & 255)
                b >>= 8
                n -= 8
            v = -1
    if v >= 0:
        out.append((b | v << n) & 255)
    return bytes(out)

raw = base91_decode(s)
Path("stage4.bin").write_bytes(raw)
print("base91 decoded len:", len(raw))
print("head hex:", raw[:32].hex())

m = FLAG_RE.search(raw)
print("flag in raw?", m.group(0) if m else None)

def try_decompress(tag, fn):
    try:
        d = fn(raw)
        print(f"[OK] {tag} len={len(d)} head={d[:80]!r}")
        mm = FLAG_RE.search(d)
        if mm:
            print("FLAG:", mm.group(0))
    except Exception:
        pass

try_decompress("zlib", lambda x: zlib.decompress(x))
try_decompress("zlib_raw(-15)", lambda x: zlib.decompress(x, wbits=-15))
try_decompress("gzip", gzip.decompress)
try_decompress("bz2", bz2.decompress)
try_decompress("lzma", lzma.decompress)

# 如果是文本
try:
    print(raw.decode("utf-8"))
except Exception:
    pass