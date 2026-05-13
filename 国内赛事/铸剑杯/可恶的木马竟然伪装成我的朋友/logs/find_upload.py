import re

print("=== 搜索6月21日晚上到6月22日早上的可疑活动 ===\n")

# 搜索6月21日晚上的POST请求
print("\n【6月21日20:00-23:59的POST请求】")
with open('ex170621.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'POST' in line and re.search(r'21/Jun/2017:(2[0-3]|1[9-9]):', line):
            print(line.strip())

# 搜索6月22日凌晨到中午的POST请求
print("\n【6月22日00:00-12:00的POST请求】")
with open('ex170622.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'POST' in line and re.search(r'22/Jun/2017:(0[0-9]|1[0-2]):', line):
            print(line.strip())

# 搜索相关的文件上传路径
print("\n【搜索上传相关的action】")
for log_file in ['ex170621.log', 'ex170622.log']:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if any(keyword in line.lower() for keyword in ['upload', 'file', '/images/', '/sxzn/images/']):
                if 'POST' in line or 'PUT' in line:
                    if re.search(r'2[12]/Jun/2017:(2[0-3]|0[0-9]|1[0-2]):', line):
                        print(f"[{log_file}] {line.strip()}")
