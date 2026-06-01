#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/extracted"

for _ in 1 2 3 4 5; do
  cat >/tmp/fdr_aslr.gdb <<'GDB'
set pagination off
set confirm off
set disable-randomization off
b *ignore_me+0x19
commands
silent
printf "page=%p checker=%p diff=%#lx\n", &page, *(void**)(&checker), (long)*(void**)(&checker)-(long)&page
quit
end
run
GDB
  gdb -q ./future_diary_revisited -x /tmp/fdr_aslr.gdb 2>/dev/null | grep 'page=' || true
done
