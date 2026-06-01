import base64
import pathlib
import re
import sys


ENC_RE = re.compile(rb"[A-Za-z0-9+/=]{16,}")
FLAG_RE = re.compile(rb"flag\{[^}]+\}", re.IGNORECASE)


def extract_flag(path: pathlib.Path):
    data = path.read_bytes()
    candidates = ENC_RE.findall(data)
    if not candidates:
        return None

    for enc in candidates:
        for pad in (b"", b"=", b"==", b"==="):
            try:
                decoded = base64.b64decode(enc + pad)
            except Exception:
                continue

            for key in range(256):
                plain = bytes(b ^ key for b in decoded)
                match = FLAG_RE.search(plain)
                if match:
                    return match.group().decode("ascii", errors="ignore"), key, enc.decode("ascii", errors="ignore")

    return None


def iter_targets(base: pathlib.Path):
    for path in sorted(base.iterdir()):
        if path.is_file() and path.suffix.lower() in {".bin", ".dat", ".txt"}:
            yield path


def main():
    base = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    found = False
    for path in iter_targets(base):
        result = extract_flag(path)
        if result:
            flag, key, enc = result
            print(f"{path.name}: {flag}  (xor_key={key}, encoded={enc})")
            found = True
        else:
            print(f"{path.name}: not found")

    if not found:
        sys.exit(1)


if __name__ == "__main__":
    main()
