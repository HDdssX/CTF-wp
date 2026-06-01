#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/extracted"

python3 - <<'PY'
from pathlib import Path

p = b""

def create(i, n, data):
    global p
    p += b"1\n%d\n%d\n" % (i, n) + data + b"\n"

def delete(i):
    global p
    p += b"2\n%d\n" % i

create(1, 0x78, b"A" * 0x78)
delete(1)
create(2, 0x78, b"B" * 0x78)
p += b"4\n"
Path("/tmp/fdr_inp").write_bytes(p)
PY

cat >/tmp/fdr_gdb <<'GDB'
set pagination off
set confirm off
break *create+0x11d
commands
silent
printf "after calloc ptr=%p\n", *(void**)($rbp-0x10)
x/8gx *(void**)($rbp-0x10)-0x10
continue
end
break *delete+0xc3
commands
silent
set $p=*(void**)(0x555555558060 + (*(int*)($rbp-0xc))*16)
printf "after free page=%d ptr=%p\n", *(int*)($rbp-0xc), $p
x/8gx $p-0x10
continue
end
run < /tmp/fdr_inp
GDB

gdb -q ./future_diary_revisited -x /tmp/fdr_gdb
