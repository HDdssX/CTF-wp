import re
import os

print("=== 深度分析banner_home.jpg相关的所有活动 ===\n")

# 查找banner_home.jpg文件大小变化的详细时间线
log_files = sorted([f for f in os.listdir('.') if f.startswith('ex170') and f.endswith('.log')])

print("【1】banner_home.jpg访问记录和文件大小变化:\n")
for log_file in log_files:
    if '170620' in log_file or '170621' in log_file or '170622' in log_file:
        print(f"\n文件: {log_file}")
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'banner_home.jpg' in line:
                    print(line.strip())

print("\n\n【2】6月20-22日所有POST请求(可能的上传):\n")
for log_file in log_files:
    if '170620' in log_file or '170621' in log_file or '170622' in log_file:
        print(f"\n文件: {log_file}")
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'POST' in line and '" 200 ' in line:  # 成功的POST
                    print(line.strip())

print("\n\n【3】查找6月20-22日访问/sxzn/路径的POST请求:\n")
for log_file in log_files:
    if '170620' in log_file or '170621' in log_file or '170622' in log_file:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'POST' in line and '/sxzn/' in line:
                    print(f"{log_file}: {line.strip()}")

print("\n\n【4】统计6月20-22日每个IP的活动:\n")
ip_stats = {}
for log_file in log_files:
    if '170620' in log_file or '170621' in log_file or '170622' in log_file:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = re.match(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    if ip not in ip_stats:
                        ip_stats[ip] = {'GET': 0, 'POST': 0, 'images': 0, 'webshell': 0}
                    
                    if 'GET' in line:
                        ip_stats[ip]['GET'] += 1
                    if 'POST' in line:
                        ip_stats[ip]['POST'] += 1
                    if '/images/' in line or 'banner_home' in line:
                        ip_stats[ip]['images'] += 1
                    if any(ext in line.lower() for ext in ['.php', '.jsp', '.asp']) and 'POST' in line:
                        ip_stats[ip]['webshell'] += 1

print("可疑IP(有POST和images访问的):")
for ip, stats in sorted(ip_stats.items(), key=lambda x: x[1]['POST'] + x[1]['images'], reverse=True):
    if stats['POST'] > 0 or stats['images'] > 0:
        print(f"{ip}: GET={stats['GET']}, POST={stats['POST']}, images={stats['images']}, webshell={stats['webshell']}")
