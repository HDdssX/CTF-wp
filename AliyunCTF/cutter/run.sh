#!/bin/bash

if [ -n "$FLAG" ]; then
    echo "$FLAG" > "/flag-$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 32).txt"
    unset FLAG
else
    echo "flag{testflag}" > "/flag-$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 32).txt"
fi

useradd -M ctf

su ctf -c 'cd /app && python app.py'