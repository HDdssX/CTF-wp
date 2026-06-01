import re

print("=== 搜索6月20日晚上(19:00-23:59)的所有活动 ===\n")

# 统计每个IP的行为
ip_activities = {}

with open('ex170620.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if re.search(r'20/Jun/2017:(1[9-9]|2[0-3]):', line):
            ip_match = re.match(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                ip = ip_match.group(1)
                if ip not in ip_activities:
                    ip_activities[ip] = {'total': 0, 'post': 0, 'webshell': 0, 'images': 0}
                ip_activities[ip]['total'] += 1
                if 'POST' in line:
                    ip_activities[ip]['post'] += 1
                if any(ext in line for ext in ['.php', '.jsp', '.asp', '.aspx']):
                    ip_activities[ip]['webshell'] += 1
                if '/images/' in line or '/sxzn/images/' in line:
                    ip_activities[ip]['images'] += 1

print("可疑IP分析(有POST或webshell尝试的):")
for ip, stats in sorted(ip_activities.items(), key=lambda x: x[1]['post']+x[1]['webshell'], reverse=True):
    if stats['post'] > 0 or stats['webshell'] > 0:
        print(f"{ip}: 总请求={stats['total']}, POST={stats['post']}, webshell尝试={stats['webshell']}, 访问images={stats['images']}")

# 详细查看可疑IP的行为
print("\n\n=== 详细查看可疑IP的POST请求 ===\n")
with open('ex170620.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if re.search(r'20/Jun/2017:(1[9-9]|2[0-3]):', line) and 'POST' in line:
            print(line.strip())
