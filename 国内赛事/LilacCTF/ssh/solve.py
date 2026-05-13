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

def simple_connect():
    """简单连接并执行命令"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 执行一些探索命令
    print("[*] 查看根目录:")
    print(exec_cmd(ssh, "ls -la /"))
    
    print("[*] 查看/etc目录:")
    print(exec_cmd(ssh, "ls -la /etc"))
    
    print("[*] 查看进程:")
    print(exec_cmd(ssh, "ps aux"))
    
    print("[*] 查看网络:")
    print(exec_cmd(ssh, "netstat -tlnp 2>/dev/null || ss -tlnp 2>/dev/null || cat /proc/net/tcp"))
    
    print("[*] 查看init脚本:")
    print(exec_cmd(ssh, "cat /init"))
    
    print("[*] 查看环境变量:")
    print(exec_cmd(ssh, "env"))
    
    ssh.close()
    print("[*] 已退出")

def proxy_jump_test():
    """测试通过ProxyJump连接"""
    # 创建到跳板机的连接
    jump_ssh = paramiko.SSHClient()
    jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 获取transport用于端口转发
    jump_transport = jump_ssh.get_transport()
    
    # 通过跳板机连接到localhost
    try:
        # 打开一个通道到localhost:22
        dest_addr = ('localhost', 22)
        local_addr = ('127.0.0.1', 0)
        channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)
        
        # 通过这个通道创建新的SSH连接
        target_ssh = paramiko.SSHClient()
        target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target_ssh.connect('localhost', username=USER, password=PASSWD, sock=channel)
        
        print("[*] 通过ProxyJump成功连接到localhost!")
        print("[*] 查看根目录:")
        print(exec_cmd(target_ssh, "ls -la /"))
        
        target_ssh.close()
    except Exception as e:
        print(f"[-] ProxyJump失败: {e}")
    
    jump_ssh.close()

def try_different_hosts():
    """尝试连接到不同的内部主机"""
    jump_ssh = paramiko.SSHClient()
    jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_ssh.connect(HOST, PORT, USER, PASSWD)
    
    jump_transport = jump_ssh.get_transport()
    
    # 尝试不同的目标
    targets = [
        ('localhost', 22),
        ('127.0.0.1', 22),
        ('10.0.2.2', 22),  # QEMU默认宿主机地址
        ('192.168.1.1', 22),
        ('host.docker.internal', 22),
    ]
    
    for target_host, target_port in targets:
        try:
            print(f"[*] 尝试连接 {target_host}:{target_port}...")
            dest_addr = (target_host, target_port)
            local_addr = ('127.0.0.1', 0)
            channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr, timeout=5)
            print(f"[+] 成功打开通道到 {target_host}:{target_port}!")
            
            # 读取SSH banner
            channel.settimeout(3)
            try:
                banner = channel.recv(1024)
                print(f"    Banner: {banner}")
            except:
                pass
            channel.close()
        except Exception as e:
            print(f"[-] 连接 {target_host}:{target_port} 失败: {e}")
    
    jump_ssh.close()

def scan_ports():
    """通过SSH隧道扫描内部端口"""
    jump_ssh = paramiko.SSHClient()
    jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_ssh.connect(HOST, PORT, USER, PASSWD)
    
    jump_transport = jump_ssh.get_transport()
    
    # 扫描localhost的常见端口
    ports = [21, 22, 23, 25, 80, 443, 2222, 3000, 5000, 8000, 8080, 9000]
    
    print("[*] 扫描localhost端口...")
    for port in ports:
        try:
            dest_addr = ('localhost', port)
            local_addr = ('127.0.0.1', 0)
            channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr, timeout=2)
            print(f"[+] 端口 {port} 开放!")
            channel.settimeout(2)
            try:
                banner = channel.recv(1024)
                print(f"    Banner: {banner[:100]}")
            except:
                pass
            channel.close()
        except Exception as e:
            pass
    
    # 扫描10.0.2.2 (QEMU宿主机)
    print("\n[*] 扫描10.0.2.2端口...")
    for port in ports:
        try:
            dest_addr = ('10.0.2.2', port)
            local_addr = ('127.0.0.1', 0)
            channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr, timeout=2)
            print(f"[+] 10.0.2.2:{port} 开放!")
            channel.settimeout(2)
            try:
                banner = channel.recv(1024)
                print(f"    Banner: {banner[:100]}")
            except:
                pass
            channel.close()
        except Exception as e:
            pass
    
    jump_ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 开始探索SSH环境")
    print("="*50)
    
    print("\n[1] 简单连接测试")
    simple_connect()
    
    print("\n[2] 尝试不同主机")
    try_different_hosts()
    
    print("\n[3] 端口扫描")
    scan_ports()
