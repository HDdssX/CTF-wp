import paramiko
import socket
import time
import sys
import hashlib

"""
重要发现：
1. 嵌套SSH到localhost可以成功认证（因为都是dropbear）
2. 但命令输出为空

这意味着dropbear在处理嵌套连接时有特殊行为。

让我重新思考FakeJumpServer攻击：
在真正的攻击中，攻击者会：
1. 等待受害者通过跳板机连接
2. 伪装成目标服务器
3. 捕获受害者的密码

在这个CTF中：
- 我们控制的是"受害者"的角色
- 我们需要找到一种方法来利用这个伪装

也许关键不在于捕获密码，而在于利用SSH的某种特性：
1. Agent Forwarding - 如果dropbear转发我们的agent到它自己，会发生什么？
2. X11 Forwarding
3. Subsystem请求

让我尝试启用Agent Forwarding看看会发生什么
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def test_agent_forwarding():
    """测试Agent Forwarding"""
    print("[*] 测试Agent Forwarding")
    
    # 检查本地是否有agent
    import os
    agent_sock = os.environ.get('SSH_AUTH_SOCK')
    print(f"本地SSH_AUTH_SOCK: {agent_sock}")
    
    # 即使没有本地agent，我们也可以尝试请求转发
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 请求agent转发
    try:
        agent_handler = paramiko.agent.AgentRequestHandler(transport.open_session())
        print("Agent转发请求成功")
    except Exception as e:
        print(f"Agent转发请求失败: {e}")
    
    # 检查远程是否有agent socket
    try:
        stdin, stdout, stderr = ssh.exec_command("echo $SSH_AUTH_SOCK; ls -la /tmp/ssh-* 2>/dev/null", timeout=5)
        result = stdout.read().decode() + stderr.read().decode()
        print(f"远程SSH环境:\n{result}")
    except Exception as e:
        print(f"错误: {e}")
    
    ssh.close()

def test_x11_forwarding():
    """测试X11 Forwarding"""
    print("\n[*] 测试X11 Forwarding")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    channel = transport.open_session()
    
    try:
        # 请求X11转发
        result = channel.request_x11()
        print(f"X11转发结果: {result}")
    except Exception as e:
        print(f"X11转发失败: {e}")
    
    channel.close()
    ssh.close()

def test_special_channels():
    """测试特殊通道"""
    print("\n[*] 测试特殊SSH通道")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试不同类型的通道
    channel_types = [
        "session",
        "x11",
        "forwarded-tcpip",
        "direct-tcpip",
        "auth-agent@openssh.com",
        "direct-streamlocal@openssh.com",
    ]
    
    for channel_type in channel_types:
        print(f"\n尝试通道类型: {channel_type}")
        
        try:
            if channel_type == "direct-tcpip":
                channel = transport.open_channel("direct-tcpip", ("localhost", 22), ('127.0.0.1', 0), timeout=5)
            elif channel_type == "direct-streamlocal@openssh.com":
                # Unix socket转发
                channel = transport.open_channel("direct-streamlocal@openssh.com", "/var/run/sshd.sock", "", timeout=5)
            elif channel_type == "auth-agent@openssh.com":
                # Agent通道
                channel = transport.open_channel("auth-agent@openssh.com", "", "", timeout=5)
            elif channel_type == "forwarded-tcpip":
                # 这需要先设置端口转发
                port = transport.request_port_forward('', 0)
                print(f"  请求的端口: {port}")
                channel = None
            else:
                channel = transport.open_channel(channel_type, timeout=5)
            
            if channel:
                print(f"  通道打开成功")
                channel.close()
            
        except Exception as e:
            print(f"  失败: {e}")
    
    ssh.close()

def test_environment_request():
    """测试环境变量请求"""
    print("\n[*] 测试环境变量设置")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    channel = transport.open_session()
    
    # 尝试设置环境变量
    env_vars = [
        ("TEST_VAR", "test_value"),
        ("PATH", "/bin:/usr/bin"),
        ("SSH_AUTH_SOCK", "/tmp/test"),
        ("FLAG", "test"),
        ("LD_PRELOAD", "/tmp/test.so"),
    ]
    
    for name, value in env_vars:
        try:
            result = channel.set_environment_variable(name, value)
            print(f"  {name}={value}: {result}")
        except Exception as e:
            print(f"  {name}: 失败 - {e}")
    
    channel.close()
    ssh.close()

def deep_analyze_dropbear_behavior():
    """深入分析dropbear行为"""
    print("\n[*] 深入分析dropbear行为")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 分析transport的各种属性
    print(f"远程版本: {transport.remote_version}")
    print(f"本地版本: {transport.local_version}")
    
    # 获取会话信息
    print(f"会话ID: {transport.get_hexdump()[:50] if hasattr(transport, 'get_hexdump') else 'N/A'}...")
    
    # 检查服务器支持的功能
    security_options = transport.get_security_options()
    print(f"安全选项类型: {type(security_options)}")
    
    # 尝试获取更多信息
    try:
        ext_info = transport.get_security_options()
        print(f"扩展信息: {ext_info}")
    except:
        pass
    
    ssh.close()

def test_signal_and_exit():
    """测试信号和退出状态"""
    print("\n[*] 测试信号和退出状态")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试发送信号
    channel = transport.open_session()
    channel.exec_command("sleep 1 && echo done")
    
    time.sleep(0.5)
    
    # 尝试发送信号
    signals = ["INT", "TERM", "HUP", "KILL", "USR1", "USR2"]
    for sig in signals:
        try:
            channel.send_signal(sig)
            print(f"  发送信号 {sig}: 成功")
        except Exception as e:
            print(f"  发送信号 {sig}: 失败 - {e}")
    
    channel.close()
    ssh.close()

def test_window_change():
    """测试窗口大小变更"""
    print("\n[*] 测试窗口大小变更")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    channel = transport.open_session()
    channel.get_pty()
    channel.invoke_shell()
    
    time.sleep(0.5)
    
    # 尝试调整窗口大小
    try:
        channel.resize_pty(80, 24)
        print("  窗口大小调整成功")
    except Exception as e:
        print(f"  窗口大小调整失败: {e}")
    
    # 检查初始输出
    if channel.recv_ready():
        output = channel.recv(4096)
        print(f"  Shell输出: {output[:200]}")
    
    channel.close()
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] SSH特性深度探索")
    print("="*60)
    
    test_agent_forwarding()
    test_x11_forwarding()
    test_special_channels()
    test_environment_request()
    deep_analyze_dropbear_behavior()
    test_signal_and_exit()
    test_window_change()
