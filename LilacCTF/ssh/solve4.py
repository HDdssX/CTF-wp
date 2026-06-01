import paramiko
import socket
import time
import sys

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(ssh, cmd, timeout=10):
    """执行命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + err

def check_outer_environment():
    """检查外部环境 - 尝试通过SSH到宿主机的不同方式"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 扫描更多端口看看有没有其他服务
    print("[*] 扫描更多内部端口...")
    for port in range(20, 100):
        try:
            channel = transport.open_channel("direct-tcpip", ('localhost', port), ('127.0.0.1', 0), timeout=1)
            print(f"[+] localhost:{port} 开放")
            channel.settimeout(1)
            try:
                data = channel.recv(256)
                print(f"    Data: {data[:100]}")
            except:
                pass
            channel.close()
        except:
            pass
    
    # 检查是否能访问QEMU的virtio端口或其他虚拟化相关端口
    print("\n[*] 检查特殊端口...")
    special_ports = [564, 6556, 9000, 9001, 9999]  # 9p端口等
    for port in special_ports:
        for host in ['localhost', '10.0.2.2', '10.0.2.15']:
            try:
                channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=2)
                print(f"[+] {host}:{port} 开放")
                channel.close()
            except:
                pass
    
    ssh.close()

def test_ssh_subsystem():
    """测试SSH子系统"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试请求不同的子系统
    subsystems = ['sftp', 'scp', 'netconf', 'shell']
    for sub in subsystems:
        try:
            channel = transport.open_session()
            channel.invoke_subsystem(sub)
            print(f"[+] 子系统 {sub} 可用")
            channel.close()
        except Exception as e:
            print(f"[-] 子系统 {sub}: {e}")
    
    ssh.close()

def test_channel_types():
    """测试不同的SSH通道类型"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试StreamLocalForward (Unix socket转发)
    print("[*] 测试Unix socket转发...")
    try:
        # 尝试连接到/run/host/notify (从环境变量看到的NOTIFY_SOCKET)
        channel = transport.open_channel("direct-streamlocal@openssh.com", 
                                         "/run/host/notify", 
                                         ("", 0))
        print("[+] Unix socket转发可用!")
        channel.close()
    except Exception as e:
        print(f"[-] Unix socket转发: {e}")
    
    # 尝试其他socket路径
    socket_paths = [
        "/run/host/notify",
        "/var/run/docker.sock",
        "/run/containerd/containerd.sock",
        "/tmp/.X11-unix/X0",
    ]
    
    for path in socket_paths:
        try:
            channel = transport.open_channel("direct-streamlocal@openssh.com", 
                                             path, 
                                             ("", 0))
            print(f"[+] Socket {path} 可访问!")
            channel.close()
        except Exception as e:
            pass
    
    ssh.close()

def explore_run_host():
    """探索/run/host目录"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    cmds = [
        "ls -laR /run/host/",
        "cat /run/host/os-release",
        "ls -la /run/host/unix-export/",
        "ls -la /run/host/incoming/",
    ]
    
    for cmd in cmds:
        print(f"\n[*] {cmd}")
        print(exec_cmd(ssh, cmd))
    
    ssh.close()

def try_escape_via_proc():
    """尝试通过/proc逃逸"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查是否能访问host的信息
    cmds = [
        "cat /proc/1/cgroup",
        "cat /proc/1/status",
        "ls -la /proc/1/root/",
        "cat /proc/1/mountinfo",
    ]
    
    for cmd in cmds:
        print(f"\n[*] {cmd}")
        print(exec_cmd(ssh, cmd))
    
    ssh.close()

def test_direct_tcpip_to_outer():
    """尝试通过SSH隧道到达外部环境"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试连接到各种可能的宿主地址
    hosts = [
        ('10.0.2.2', 22),  # QEMU gateway
        ('172.17.0.1', 22),  # Docker gateway
        ('192.168.122.1', 22),  # libvirt default
        ('host.containers.internal', 22),
    ]
    
    for host, port in hosts:
        try:
            print(f"[*] 尝试 {host}:{port}...")
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=3)
            print(f"[+] 成功连接到 {host}:{port}")
            channel.settimeout(2)
            banner = channel.recv(100)
            print(f"    Banner: {banner}")
            channel.close()
        except Exception as e:
            print(f"[-] {host}:{port}: {e}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 深度探索")
    print("="*50)
    
    print("\n[1] 探索/run/host目录")
    explore_run_host()
    
    print("\n[2] 尝试通过/proc逃逸")
    try_escape_via_proc()
    
    print("\n[3] 测试SSH子系统")
    test_ssh_subsystem()
    
    print("\n[4] 测试通道类型")
    test_channel_types()
    
    print("\n[5] 测试direct-tcpip到外部")
    test_direct_tcpip_to_outer()
