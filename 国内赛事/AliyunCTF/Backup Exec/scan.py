#!/usr/bin/env python3
import socket

target = '116.62.114.4'
ports = [21, 135, 389, 636, 445, 139, 3389, 5985, 62831, 69128, 67540, 60325, 63588]

print(f"Scanning {target}...")
for port in ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((target, port))
        status = 'OPEN' if result == 0 else f'CLOSED ({result})'
        print(f'Port {port}: {status}')
        sock.close()
    except Exception as e:
        print(f'Port {port}: ERROR - {e}')
