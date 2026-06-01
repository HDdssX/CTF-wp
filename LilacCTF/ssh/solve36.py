import paramiko
import socket
import time
import sys

"""
关键观察：
"Directory tree /var/lib/machines/rootfs is currently busy"

这意味着：
1. 容器使用的是 /var/lib/machines/rootfs 作为根文件系统
2. 它可能被其他进程使用
3. 这是systemd-nspawn的典型行为

让我重新思考题目：
1. 题目名字是 "very_good_ssh"
2. 提示是利用SSH特性，不是漏洞
3. 类似阿里云CTF 2025 FakeJumpServer
4. "第二次连接的错误信息有用"

等等！"第二次连接的错误信息有用"！

如果我们尝试通过ProxyJump连接到某个目标，
第二次连接（即通过跳板机到目标的连接）的错误信息可能会泄露信息！

让我尝试通过直接SSH命令来测试ProxyJump
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def test_proxyjump_error():
    """测试ProxyJump的错误信息"""
    import subprocess
    
    print("[*] 测试ProxyJump错误信息")
    
    # 测试不同的目标
    targets = [
        "localhost",
        "127.0.0.1",
        "172.17.0.1",
        "10.0.2.2",
    ]
    
    for target in targets:
        print(f"\n=== 目标: {target} ===")
        
        # 使用sshpass来提供密码
        # 或者使用expect脚本
        cmd = f'echo "123456" | ssh -o StrictHostKeyChecking=no -o BatchMode=no -J ctf@{HOST}:{PORT} ctf@{target} id 2>&1'
        
        print(f"命令: {cmd}")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("超时")
        except Exception as e:
            print(f"错误: {e}")

def test_with_verbose_ssh():
    """使用verbose模式的SSH测试"""
    import subprocess
    
    print("\n[*] 使用verbose SSH测试")
    
    # 先测试直接连接
    print("\n--- 直接连接到跳板机 ---")
    cmd = f'ssh -v -o StrictHostKeyChecking=no -o ConnectTimeout=10 ctf@{HOST} -p {PORT} "id" 2>&1'
    
    try:
        # 由于需要输入密码，这可能不会工作
        # 但我们可以看到连接过程
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        print(f"结果: {result.stdout[:1000] if result.stdout else ''}")
    except:
        pass

def analyze_direct_tcpip_error():
    """分析direct-tcpip的错误"""
    print("\n[*] 分析direct-tcpip错误")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试各种目标地址
    test_addresses = [
        ("localhost", 22),
        ("127.0.0.1", 22),
        ("172.17.0.1", 22),
        ("10.0.2.2", 22),
        ("192.168.1.1", 22),  # 不存在的地址
        ("google.com", 22),   # 外部地址
        ("8.8.8.8", 22),      # 外部IP
    ]
    
    for host, port in test_addresses:
        print(f"\n尝试 {host}:{port}...")
        
        try:
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
            channel.settimeout(5)
            
            # 读取banner
            data = channel.recv(256)
            print(f"  成功! 数据: {data[:100]}")
            
            channel.close()
            
        except Exception as e:
            print(f"  失败: {e}")
    
    ssh.close()

def test_special_forward_requests():
    """测试特殊的转发请求"""
    print("\n[*] 测试特殊转发请求")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试一些特殊的目标
    special_targets = [
        # Unix socket路径（如果支持streamlocal）
        # 空主机名
        ("", 22),
        # 特殊IP
        ("0", 22),
        ("255.255.255.255", 22),
        # IPv6
        ("::1", 22),
        ("::ffff:127.0.0.1", 22),
        # 主机名变体
        ("LOCALHOST", 22),
        ("Localhost", 22),
        # URL编码
        ("127%2e0%2e0%2e1", 22),
    ]
    
    for host, port in special_targets:
        try:
            print(f"\n尝试 '{host}':{port}...")
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=3)
            channel.settimeout(3)
            
            data = channel.recv(256)
            print(f"  成功! 数据: {data[:50]}")
            
            channel.close()
        except Exception as e:
            error_str = str(e)
            print(f"  失败: {error_str[:100]}")
    
    ssh.close()

def analyze_ubuntu_ssh_config():
    """分析Ubuntu主机的SSH配置"""
    print("\n[*] 分析172.17.0.1的SSH行为")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 连接到Ubuntu
    channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=10)
    channel.settimeout(30)
    
    # 读取banner
    banner = b""
    while True:
        byte = channel.recv(1)
        if not byte:
            break
        banner += byte
        if byte == b"\n":
            break
    
    print(f"Banner: {banner}")
    
    # 发送我们的banner
    channel.send(b"SSH-2.0-TestClient\r\n")
    
    # 读取KEX_INIT
    time.sleep(0.5)
    kex_data = channel.recv(4096)
    
    print(f"收到KEX数据: {len(kex_data)} bytes")
    
    # 解析KEX_INIT来查看支持的算法
    if len(kex_data) > 5:
        # SSH packet: [length:4][padding:1][type:1][payload:...]
        # KEX_INIT payload includes:
        # - cookie[16]
        # - kex_algorithms
        # - server_host_key_algorithms
        # - encryption_algorithms_client_to_server
        # - encryption_algorithms_server_to_client
        # - mac_algorithms_client_to_server
        # - mac_algorithms_server_to_client
        # - compression_algorithms_client_to_server
        # - compression_algorithms_server_to_client
        # - languages_client_to_server
        # - languages_server_to_client
        # - first_kex_packet_follows
        # - reserved
        
        packet_len = int.from_bytes(kex_data[0:4], 'big')
        padding_len = kex_data[4]
        msg_type = kex_data[5]
        
        if msg_type == 20:  # SSH_MSG_KEXINIT
            # 跳过cookie (16 bytes)
            offset = 6 + 16
            
            # 读取kex算法
            def read_string(data, off):
                length = int.from_bytes(data[off:off+4], 'big')
                return data[off+4:off+4+length].decode(), off + 4 + length
            
            try:
                kex_algos, offset = read_string(kex_data, offset)
                print(f"\nKEX算法: {kex_algos[:200]}")
                
                host_key_algos, offset = read_string(kex_data, offset)
                print(f"主机密钥算法: {host_key_algos}")
                
                enc_algos_c2s, offset = read_string(kex_data, offset)
                print(f"加密算法(c2s): {enc_algos_c2s[:100]}")
            except Exception as e:
                print(f"解析错误: {e}")
    
    channel.close()
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入SSH分析 v2")
    print("="*60)
    
    analyze_direct_tcpip_error()
    
    print("\n" + "="*60)
    test_special_forward_requests()
    
    print("\n" + "="*60)
    analyze_ubuntu_ssh_config()
