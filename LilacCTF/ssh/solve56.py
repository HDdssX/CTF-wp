#!/usr/bin/env python3
"""
探索新环境 61.147.171.35:58677
"""

import paramiko
import time

TARGET_HOST = "61.147.171.35"
TARGET_PORT = 58677
USERNAME = "ctf"
PASSWORD = "123456"

def run_cmd(cmd):
    """执行命令并返回结果"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(TARGET_HOST, TARGET_PORT, USERNAME, PASSWORD, timeout=10)
    
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    client.close()
    return out, err

def explore():
    print("=" * 70)
    print(f"[*] 探索环境 {TARGET_HOST}:{TARGET_PORT}")
    print("=" * 70)
    
    commands = [
        ("id", "当前用户"),
        ("uname -a", "系统信息"),
        ("cat /etc/passwd", "用户列表"),
        ("ls -la /", "根目录"),
        ("ls -la /root", "root目录"),
        ("ls -la /etc", "etc目录"),
        ("cat /init", "init脚本"),
        ("env", "环境变量"),
        ("mount", "挂载点"),
        ("cat /proc/1/cmdline", "PID 1命令"),
        ("cat /proc/1/cgroup", "cgroup信息"),
        ("ip addr", "网络配置"),
        ("cat /etc/hostname", "主机名"),
    ]
    
    for cmd, desc in commands:
        print(f"\n[*] {desc}: {cmd}")
        print("-" * 50)
        try:
            out, err = run_cmd(cmd)
            if out:
                print(out[:500])
            if err:
                print(f"[stderr] {err[:200]}")
        except Exception as e:
            print(f"[!] 错误: {e}")

def test_direct_tcpip():
    """测试direct-tcpip通道"""
    print("\n" + "=" * 70)
    print("[*] 测试direct-tcpip通道")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(TARGET_HOST, TARGET_PORT, USERNAME, PASSWORD, timeout=10)
    
    transport = client.get_transport()
    
    targets = [
        ("localhost", 22),
        ("127.0.0.1", 22),
        ("172.17.0.1", 22),
        ("10.42.0.1", 22),
    ]
    
    for host, port in targets:
        print(f"\n[*] 尝试连接 {host}:{port}")
        try:
            channel = transport.open_channel(
                "direct-tcpip",
                (host, port),
                ("127.0.0.1", 0)
            )
            channel.settimeout(3)
            banner = channel.recv(1024)
            print(f"    Banner: {banner.decode(errors='replace').strip()}")
            channel.close()
        except Exception as e:
            print(f"    错误: {e}")
    
    client.close()

def test_nested_ssh():
    """通过direct-tcpip测试嵌套SSH"""
    print("\n" + "=" * 70)
    print("[*] 通过direct-tcpip进行嵌套SSH")
    print("=" * 70)
    
    # 第一层连接
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(TARGET_HOST, TARGET_PORT, USERNAME, PASSWORD, timeout=10)
    
    transport1 = client1.get_transport()
    print(f"[1] 连接到 {TARGET_HOST}:{TARGET_PORT}")
    print(f"    Host Key: {transport1.get_remote_server_key().get_fingerprint().hex()}")
    
    # 通过direct-tcpip连接到localhost:22
    print("\n[*] 打开direct-tcpip通道到localhost:22")
    channel = transport1.open_channel(
        "direct-tcpip",
        ("localhost", 22),
        ("127.0.0.1", 0)
    )
    
    # 在这个通道上建立第二层SSH
    transport2 = paramiko.Transport(channel)
    transport2.connect()
    print(f"[2] 通过通道连接到localhost")
    print(f"    Host Key: {transport2.get_remote_server_key().get_fingerprint().hex()}")
    
    # 尝试认证
    try:
        transport2.auth_password(USERNAME, PASSWORD)
        print(f"    认证成功!")
        
        # 执行命令
        chan = transport2.open_channel("session")
        chan.exec_command("id; hostname; cat /proc/1/cmdline")
        time.sleep(1)
        output = chan.recv(4096).decode(errors='replace')
        print(f"    Output: {output}")
        chan.close()
        
    except paramiko.AuthenticationException:
        print(f"    认证失败")
    except Exception as e:
        print(f"    错误: {e}")
    
    transport2.close()
    client1.close()

def test_real_host_ssh():
    """通过direct-tcpip连接到真实主机172.17.0.1"""
    print("\n" + "=" * 70)
    print("[*] 通过direct-tcpip连接真实主机172.17.0.1")
    print("=" * 70)
    
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(TARGET_HOST, TARGET_PORT, USERNAME, PASSWORD, timeout=10)
    
    transport1 = client1.get_transport()
    
    # 通过direct-tcpip连接到172.17.0.1:22
    print("[*] 打开direct-tcpip通道到172.17.0.1:22")
    channel = transport1.open_channel(
        "direct-tcpip",
        ("172.17.0.1", 22),
        ("127.0.0.1", 0)
    )
    
    # 在这个通道上建立SSH
    transport2 = paramiko.Transport(channel)
    transport2.connect()
    print(f"    Host Key: {transport2.get_remote_server_key().get_fingerprint().hex()}")
    print(f"    Server: {transport2.remote_version}")
    
    # 获取支持的认证方法
    try:
        transport2.auth_none("root")
    except paramiko.BadAuthenticationType as e:
        print(f"    支持的认证方法: {e.allowed_types}")
    except:
        pass
    
    transport2.close()
    client1.close()

if __name__ == "__main__":
    explore()
    test_direct_tcpip()
    test_nested_ssh()
    test_real_host_ssh()
