#!/bin/bash

set -euo pipefail

HEX=$(head -c 16 /dev/urandom | xxd -p)
FLAG="ISCTF{${HEX}}"

echo -n "${FLAG}" > /flag
chown www-data:www-data /flag
chmod 440 /flag

echo $FLAG
echo "==> run done"
exec "$@"



