#!/bin/bash
echo $FLAG > /flag
unset FLAG
python mcp_server.py &
python main.py