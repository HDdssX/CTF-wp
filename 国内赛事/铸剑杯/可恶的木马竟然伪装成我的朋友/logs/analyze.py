import re
import os
from datetime import datetime

# 搜索包含banner_home.jpg的所有记录,并检查文件大小变化
banner_records = []

log_files = [f for f in os.listdir('.') if f.startswith('ex17062')]  # 6月20-29日的日志
log_files.sort()

for log_file in log_files:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'banner_home.jpg' in line and ' 200 ' in line:
                # 提取日期和文件大小
                match = re.search(r'\[(\d+/\w+/\d+:\d+:\d+:\d+)', line)
                size_match = re.search(r' 200 (\d+)', line)
                if match and size_match:
                    date_str = match.group(1)
                    size = size_match.group(1)
                    banner_records.append((log_file, date_str, size, line.strip()))

# 打印找到的记录
print("=== Banner_home.jpg访问记录(文件大小变化) ===\n")
prev_size = None
for record in banner_records[:30]:  # 只显示前30条
    log_file, date_str, size, line = record
    if prev_size and size != prev_size:
        print(f"\n*** 文件大小变化: {prev_size} -> {size} ***\n")
    print(f"[{log_file}] Size:{size} - {date_str}")
    prev_size = size

print(f"\n总共找到 {len(banner_records)} 条记录")
