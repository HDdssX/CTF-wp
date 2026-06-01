import re

print("=== 搜索6月21日晚上(18:00-23:59)与banner_home.jpg相关的POST请求 ===\n")

with open('ex170621.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if re.search(r'21/Jun/2017:(1[8-9]|2[0-3]):', line) and 'POST' in line:
            print(line.strip())

print("\n\n=== 搜索6月21日晚上所有POST请求 ===\n")
with open('ex170621.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if re.search(r'21/Jun/2017:(1[8-9]|2[0-3]):', line) and 'POST' in line:
            ip_match = re.match(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                print(f"IP: {ip_match.group(1)}, {line.strip()}")

print("\n\n=== 检查是否有multipart/form-data上传请求 ===\n")            
with open('ex170621.log', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    if 'multipart' in content.lower() or 'upload' in content.lower():
        print("发现上传相关内容!")
        for line in content.split('\n'):
            if 'multipart' in line.lower() or 'upload' in line.lower():
                print(line)
    else:
        print("未发现明显的上传请求")
