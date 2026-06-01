import paramiko
import socket
import time
import sys
import threading
import struct

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

def analyze_dropbear_behavior():
    """
    分析dropbear的特殊行为
    
    FakeJumpServer攻击的核心是：当客户端通过跳板机连接时，
    跳板机可以伪造目标服务器的响应
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 获取跳板机（dropbear）的host key
    jumphost_key = transport.get_remote_server_key()
    print(f"[*] 跳板机 host key: {jumphost_key.get_fingerprint().hex()}")
    print(f"[*] Key type: {jumphost_key.get_name()}")
    
    # 尝试直接转发到localhost:22看看是什么
    print("\n[*] 测试direct-tcpip到localhost:22...")
    
    try:
        channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0))
        
        # 读取SSH banner
        data = channel.recv(1024)
        print(f"[*] localhost:22 banner: {data}")
        
        channel.close()
    except Exception as e:
        print(f"[-] 错误: {e}")
    
    # 检查dropbear的配置
    print("\n[*] 检查dropbear相关文件...")
    for path in ["/etc/dropbear", "/usr/sbin/dropbear", "/var/run"]:
        result = exec_cmd(ssh, f"ls -la {path}")
        print(f"{path}: {result}")
    
    ssh.close()

def test_proxycommand_behavior():
    """
    测试代理命令行为
    
    当使用ssh -J时，客户端会：
    1. 连接到跳板机
    2. 通过direct-tcpip通道连接到目标
    3. 在通道上进行SSH握手
    
    问题是：跳板机可以修改通道中的数据！
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试通过跳板机连接到10.0.2.2:22...")
    
    channel = transport.open_channel("direct-tcpip", ("10.0.2.2", 22), ('127.0.0.1', 0))
    
    # 读取banner
    data = channel.recv(1024)
    print(f"[*] 10.0.2.2:22 banner: {data}")
    
    # 发送我们的banner
    channel.send(b"SSH-2.0-paramiko_test\r\n")
    
    # 读取key exchange init
    kex_data = channel.recv(4096)
    print(f"[*] KEX数据长度: {len(kex_data)}")
    
    # SSH包格式: [4字节长度][1字节padding长度][payload][padding][MAC]
    if len(kex_data) > 5:
        pkt_len = struct.unpack(">I", kex_data[:4])[0]
        pad_len = kex_data[4]
        msg_type = kex_data[5]
        print(f"[*] 包长度: {pkt_len}, padding: {pad_len}, 消息类型: {msg_type}")
        
        # 消息类型20 = SSH_MSG_KEXINIT
        if msg_type == 20:
            print("[*] 收到KEXINIT包")
    
    channel.close()
    ssh.close()

def check_ssh_subsystems():
    """检查SSH子系统配置"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查可能的SSH配置...")
    
    for path in [
        "/etc/ssh/sshd_config",
        "/etc/dropbear",
        "/proc/*/cmdline"
    ]:
        result = exec_cmd(ssh, f"cat {path}")
        if result.strip() and "No such file" not in result:
            print(f"\n{path}:")
            print(result)
    
    # 查看dropbear进程参数
    print("\n[*] 进程信息:")
    result = exec_cmd(ssh, "cat /proc/1/cmdline | tr '\\0' ' '")
    print(f"PID 1: {result}")
    
    result = exec_cmd(ssh, "ps aux")
    print(result)
    
    ssh.close()

def test_banner_injection():
    """
    测试banner注入
    
    如果我们能控制通道中的数据，可能可以注入SSH banner来欺骗客户端
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试连接到一个不存在的端口，看看dropbear如何处理
    print("[*] 测试连接到不存在的端口...")
    
    for port in [1, 2, 80, 443]:
        try:
            channel = transport.open_channel("direct-tcpip", ("127.0.0.1", port), ('127.0.0.1', 0), timeout=3)
            data = channel.recv(1024, timeout=2)
            print(f"Port {port}: {data}")
            channel.close()
        except Exception as e:
            print(f"Port {port}: {e}")
    
    ssh.close()

def test_stderr_channel():
    """
    测试stderr通道
    
    题目提示"第二次SSH连接的报错也是有用的提示"
    让我们看看错误信息
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 执行可能产生错误的命令...")
    
    # 尝试运行ssh命令
    commands = [
        "ssh",
        "dbclient",
        "dropbear",
        "nc",
        "telnet",
        "exec ssh 127.0.0.1",
        "2>&1 ssh 127.0.0.1"
    ]
    
    for cmd in commands:
        print(f"\n[*] 命令: {cmd}")
        result = exec_cmd(ssh, cmd)
        print(f"结果: {result[:200]}")
    
    ssh.close()

def check_file_descriptors():
    """检查文件描述符"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查文件描述符...")
    result = exec_cmd(ssh, "ls -la /proc/self/fd/")
    print(result)
    
    print("[*] 检查/proc/self/fdinfo/...")
    result = exec_cmd(ssh, "cat /proc/self/fdinfo/*")
    print(result)
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 深入分析SSH行为")
    print("="*50)
    
    print("\n[1] 分析dropbear行为")
    analyze_dropbear_behavior()
    
    print("\n[2] 测试ProxyCommand行为")
    test_proxycommand_behavior()
    
    print("\n[3] 检查SSH子系统")
    check_ssh_subsystems()
    
    print("\n[4] 检查文件描述符")
    check_file_descriptors()
