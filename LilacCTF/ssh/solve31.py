import paramiko
import socket
import time
import sys

"""
回顾提示：
1. 这是SSH特性利用题，不是漏洞利用
2. 类似阿里云CTF 2025 FakeJumpServer
3. 第二次SSH连接的错误信息有用
4. 用户名/密码注入无关

FakeJumpServer攻击的核心：
- 当用户通过跳板机连接时，跳板机可以MITM攻击
- 关键是捕获用户的认证信息

在这个场景中：
- dropbear在容器外运行
- dropbear处理direct-tcpip请求
- 当我们请求转发到localhost:22时，dropbear实际上返回的是自己

这意味着：
如果我们用ssh -J (ProxyJump)通过这个跳板机连接到"localhost"
dropbear会让我们连接到自己，并可能捕获我们的密码！

但是等等...我们需要的是捕获*别人*的密码，或者找到已存储的凭据

让我检查SSH Agent Forwarding
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

def check_ssh_agent():
    """检查SSH Agent"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查SSH Agent环境变量")
    
    # 检查SSH Agent相关环境变量
    result = exec_cmd(ssh, "env | grep -i ssh")
    print(f"SSH环境变量:\n{result}")
    
    result = exec_cmd(ssh, "echo $SSH_AUTH_SOCK")
    print(f"SSH_AUTH_SOCK: {result}")
    
    result = exec_cmd(ssh, "ls -la /tmp/ssh-* 2>/dev/null")
    print(f"/tmp/ssh-*: {result}")
    
    ssh.close()

def check_ssh_with_agent():
    """尝试带Agent Forwarding的连接"""
    
    # 尝试使用agent forwarding连接
    print("\n[*] 尝试Agent Forwarding")
    
    # 首先，检查本地是否有ssh-agent
    import subprocess
    try:
        result = subprocess.run(['ssh-add', '-l'], capture_output=True, text=True, timeout=5)
        print(f"本地SSH Agent: {result.stdout} {result.stderr}")
    except:
        print("本地没有SSH Agent或ssh-add不可用")

def check_env_variables():
    """检查所有环境变量"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("\n[*] 检查所有环境变量")
    
    result = exec_cmd(ssh, "env")
    print(f"环境变量:\n{result}")
    
    ssh.close()

def check_proc_info():
    """检查/proc信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("\n[*] 检查/proc信息")
    
    # 检查当前进程
    result = exec_cmd(ssh, "cat /proc/self/status")
    print(f"/proc/self/status:\n{result[:1000]}")
    
    # 检查cmdline
    result = exec_cmd(ssh, "cat /proc/self/cmdline | tr '\\0' ' '")
    print(f"cmdline: {result}")
    
    # 检查父进程
    result = exec_cmd(ssh, "cat /proc/self/stat")
    print(f"stat: {result}")
    
    ssh.close()

def try_port_forward_auth():
    """
    尝试通过端口转发进行认证测试
    
    思路：如果dropbear伪造localhost:22的响应，
    它可能也在记录认证尝试
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 通过端口转发测试认证")
    
    # 打开到localhost:22的通道
    channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0), timeout=5)
    channel.settimeout(5)
    
    # 读取banner
    banner = channel.recv(1024)
    print(f"Banner: {banner}")
    
    # 尝试创建一个新的SSH连接通过这个通道
    # 这模拟了ProxyJump的行为
    
    channel.close()
    ssh.close()

def nested_ssh_test():
    """嵌套SSH测试"""
    
    print("\n[*] 嵌套SSH测试")
    
    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(HOST, PORT, USER, PASSWD)
    
    transport1 = ssh1.get_transport()
    
    # 打开到localhost:22的通道
    channel = transport1.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0), timeout=5)
    
    # 创建一个socket-like包装
    class ChannelWrapper:
        def __init__(self, channel):
            self.channel = channel
        
        def recv(self, size):
            return self.channel.recv(size)
        
        def send(self, data):
            return self.channel.send(data)
        
        def close(self):
            self.channel.close()
        
        def settimeout(self, timeout):
            self.channel.settimeout(timeout)
        
        def makefile(self, mode, bufsize=-1):
            return self.channel.makefile(mode, bufsize)
    
    # 通过这个通道创建新的SSH连接
    try:
        ssh2 = paramiko.SSHClient()
        ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 使用通道作为socket
        transport2 = paramiko.Transport(channel)
        transport2.connect(username=USER, password=PASSWD)
        
        # 现在ssh2连接到的是哪个服务器？
        # 如果dropbear伪造了响应，这应该仍然连接到dropbear
        
        ssh2_client = paramiko.SSHClient()
        ssh2_client._transport = transport2
        
        # 执行命令
        channel2 = transport2.open_session()
        channel2.exec_command("cat /etc/hostname; cat /proc/sys/kernel/random/boot_id")
        channel2.settimeout(5)
        
        output = channel2.recv(4096).decode()
        print(f"嵌套SSH输出: {output}")
        
        channel2.close()
        transport2.close()
        
    except Exception as e:
        print(f"嵌套SSH错误: {e}")
    
    channel.close()
    ssh1.close()

def multiple_nested_test():
    """多层嵌套测试，看看有什么有趣的行为"""
    
    print("\n[*] 多层嵌套测试")
    
    for i in range(3):
        print(f"\n--- 第{i+1}层 ---")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, PORT, USER, PASSWD)
        
        # 获取一些标识信息
        result = exec_cmd(ssh, "cat /proc/sys/kernel/random/boot_id; cat /etc/machine-id 2>/dev/null; echo '---'; cat /proc/self/cgroup")
        print(f"标识: {result[:500]}")
        
        ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] SSH特性探索")
    print("="*60)
    
    check_ssh_agent()
    check_env_variables()
    check_proc_info()
    
    print("\n" + "="*60)
    print("[*] 嵌套SSH测试")
    print("="*60)
    
    nested_ssh_test()
    multiple_nested_test()
