import re

print("=== 搜索6月20日所有POST请求 ===\n")

with open('ex170620.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '20/Jun/2017' in line and 'POST' in line:
            print(line.strip())
