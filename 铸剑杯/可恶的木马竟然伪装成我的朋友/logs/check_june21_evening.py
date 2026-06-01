import re

print("=== 6月21日晚上(18:00-23:59)的所有活动 ===\n")

with open('ex170621.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# 统计晚上的所有请求
evening_requests = []
for line in lines:
    if re.search(r'21/Jun/2017:(1[8-9]|2[0-3]):', line):
        evening_requests.append(line.strip())

print(f"6月21日晚上共有 {len(evening_requests)} 条请求\n")

# 查找POST请求
print("【POST请求】:\n")
for line in evening_requests:
    if 'POST' in line:
        print(line)

# 查找webshell相关
print("\n【webshell相关请求】:\n")
for line in evening_requests:
    if any(ext in line for ext in ['.php', '.jsp', '.asp']):
        print(line)

# 统计IP
ip_counts = {}
for line in evening_requests:
    match = re.match(r'(\d+\.\d+\.\d+\.\d+)', line)
    if match:
        ip = match.group(1)
        ip_counts[ip] = ip_counts.get(ip, 0) + 1

print("\n【访问次数最多的IP】:\n")
for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{ip}: {count}次")
    
# 详细查看访问次数最多的IP的行为
print("\n【详细查看可疑IP的行为】:\n")
top_ip = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
print(f"IP {top_ip} 的详细行为:")
for line in evening_requests:
    if line.startswith(top_ip):
        print(line)
