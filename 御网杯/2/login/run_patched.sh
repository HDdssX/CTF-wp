#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
LD_LIBRARY_PATH=/tmp/lib223 setarch x86_64 -R sh -c '
./login_patched >/dev/null 2>&1 &
pid=$!
sleep 1
cat /proc/$pid/maps | egrep "login_patched|libc\.so\.6|ld223|heap"
kill -9 $pid
'
