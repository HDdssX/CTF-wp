import re
import os

print("=== 搜索6月21日晚上和6月22日早上所有可疑的sxzn相关请求 ===\n")

# 搜索包含sxzn且是POST的请求
found = []

# 6月21日晚上18:00-23:59
with open('ex170621.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if re.search(r'21/Jun/2017:(1[8-9]|2[0-3]):', line) and '/sxzn/' in line:
            if 'POST' in line or 'multipart' in line.lower() or 'Content-Length' in line:
                found.append(('2021-06-21晚', line.strip()))

# 6月22日凌晨00:00-12:00
with open('ex170622.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if re.search(r'22/Jun/2017:(0[0-9]|1[01]):', line) and '/sxzn/' in line:
            if 'POST' in line or 'multipart' in line.lower():
                found.append(('2021-06-22早', line.strip()))

print(f"找到 {len(found)} 条相关记录:\n")
for when, line in found:
    print(f"[{when}] {line}")

# 现在搜索banner_home第一次变成40920的时间点前后的所有POST请求
print("\n\n=== 搜索6月22日02:00-13:00之间的所有POST请求 ===\n")
with open('ex170622.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if re.search(r'22/Jun/2017:(0[2-9]|1[0-2]):', line) and 'POST' in line:
            print(line.strip())
