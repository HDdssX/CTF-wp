#!/bin/sh

chmod 744 /flag

cd /app
python3 app.py &
nginx -g 'daemon off;'