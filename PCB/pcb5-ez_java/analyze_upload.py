#!/usr/bin/env python3
"""
分析DashboardServlet的上传功能
从class文件中提取关键信息
"""

import subprocess
import os

# 使用javap详细查看uploadFile方法
result = subprocess.run(
    ['javap', '-c', '-p', '-v', 'DashboardServlet.class'],
    capture_output=True,
    text=True
)

# 保存完整输出
with open('DashboardServlet_full.txt', 'w', encoding='utf-8') as f:
    f.write(result.stdout)

print("[+] 完整反编译已保存到 DashboardServlet_full.txt")

# 提取uploadFile方法
lines = result.stdout.split('\n')
in_upload = False
upload_lines = []

for i, line in enumerate(lines):
    if 'uploadFile' in line:
        in_upload = True
    
    if in_upload:
        upload_lines.append(line)
        
        # 找到下一个方法开始
        if i > 0 and line.strip().startswith('private') and 'uploadFile' not in line:
            break

print("\n[*] uploadFile 方法关键代码:")
print('='*60)
for line in upload_lines[:100]:  # 前100行
    print(line)
