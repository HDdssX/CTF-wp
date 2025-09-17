import re
import os

print("=== 全面搜索所有webshell POST尝试 ===\n")

log_files = sorted([f for f in os.listdir('.') if f.startswith('ex17') and f.endswith('.log')])

webshell_attacks = []

for log_file in log_files:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # 查找POST请求到.php, .jsp, .asp文件
            if 'POST' in line and re.search(r'\.(php|jsp|asp|aspx)', line):
                # 排除正常的系统文件
                if not any(normal in line.lower() for normal in ['download.jsp', 'main.jsp', 'login', 'register', 'search', 'check']):
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+) - - \[(\d+)/(\w+)/(\d+):(\d+):(\d+):(\d+)', line)
                    if match:
                        ip, day, month, year, hour, minute, second = match.groups()
                        path_match = re.search(r'"POST ([^ ]+)', line)
                        if path_match:
                            path = path_match.group(1)
                            webshell_attacks.append({
                                'file': log_file,
                                'ip': ip,
                                'date': f"{year}-{month}-{day}",
                                'time': f"{hour}:{minute}:{second}",
                                'path': path,
                                'line': line.strip()
                            })

# 按IP和日期分组
from collections import defaultdict
attacks_by_ip_date = defaultdict(list)

for attack in webshell_attacks:
    key = (attack['ip'], attack['date'])
    attacks_by_ip_date[key].append(attack)

# 找出同一IP同一天有多个webshell尝试的
print("【找到的webshell攻击事件】:\n")
for (ip, date), attacks in sorted(attacks_by_ip_date.items(), key=lambda x: len(x[1]), reverse=True):
    if len(attacks) >= 5:  # 至少5次尝试
        print(f"\n日期: {date}")
        print(f"IP: {ip}")
        print(f"尝试次数: {len(attacks)}")
        print(f"时间段: {attacks[0]['time']} - {attacks[-1]['time']}")
        print("尝试的webshell:")
        
        webshells = []
        for attack in attacks[:20]:  # 只显示前20个
            filename = attack['path'].split('/')[-1]
            if filename not in webshells:
                webshells.append(filename)
            print(f"  [{attack['time']}] {attack['path']}")
        
        print(f"\nWebshell列表: {'-'.join(webshells)}")
        print("-" * 80)
