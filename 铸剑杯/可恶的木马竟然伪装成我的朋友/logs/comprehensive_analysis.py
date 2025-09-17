import re
import os
from datetime import datetime

print("="*80)
print("全面分析:寻找木马上传事件")
print("="*80)

# 第一步:找出banner_home.jpg文件大小变化的关键时间点
print("\n【步骤1】分析banner_home.jpg的文件大小变化\n")

log_files = sorted([f for f in os.listdir('.') if f.startswith('ex17') and f.endswith('.log')])

size_changes = []
prev_size = None
prev_date = None

for log_file in log_files:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'banner_home.jpg' in line and '" 200 ' in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+) - - \[(.+?)\] "GET /sxzn/images/banner_home.jpg HTTP/1.1" 200 (\d+)', line)
                if match:
                    ip, timestamp, size = match.groups()
                    size = int(size)
                    if prev_size is not None and size != prev_size:
                        size_changes.append({
                            'from_date': prev_date,
                            'to_date': timestamp,
                            'from_size': prev_size,
                            'to_size': size,
                            'file': log_file
                        })
                    prev_size = size
                    prev_date = timestamp

print("文件大小变化记录:")
for change in size_changes:
    print(f"  {change['from_date']} ({change['from_size']}字节) -> {change['to_date']} ({change['to_size']}字节)")

# 第二步:在文件大小变化前后查找POST请求(可能的上传行为)
print("\n【步骤2】查找文件大小变化时间段的POST请求\n")

for change in size_changes:
    # 解析日期
    to_date_str = change['to_date'].split(':')[0]  # 获取日期部分
    print(f"\n分析时间段: {to_date_str}")
    
    # 提取日期信息用于匹配日志文件
    date_match = re.search(r'(\d+)/(\w+)/(\d+)', to_date_str)
    if date_match:
        day, month, year = date_match.groups()
        
        # 月份映射
        month_map = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',
                     'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
        month_num = month_map.get(month, '00')
        
        # 构造日志文件名
        log_date = f"ex{year[2:]}{month_num}{day.zfill(2)}.log"
        
        if os.path.exists(log_date):
            print(f"  检查日志文件: {log_date}")
            
            with open(log_date, 'r', encoding='utf-8', errors='ignore') as f:
                post_requests = []
                for line in f:
                    if 'POST' in line and '" 200 ' in line:  # 只看成功的POST
                        post_requests.append(line.strip())
                
                if post_requests:
                    print(f"  发现 {len(post_requests)} 个成功的POST请求:")
                    for req in post_requests[:10]:  # 只显示前10个
                        print(f"    {req}")
                else:
                    print("  未发现成功的POST请求")

# 第三步:查找同一天访问webshell的行为
print("\n" + "="*80)
print("【步骤3】查找尝试访问webshell的行为")
print("="*80)

for log_file in log_files:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        webshell_attempts = {}
        
        for line in f:
            # 查找webshell访问尝试(.php, .jsp, .asp等)
            if re.search(r'\.(php|jsp|asp|aspx)', line, re.IGNORECASE):
                match = re.search(r'(\d+\.\d+\.\d+\.\d+) - - \[(.+?)\] "(GET|POST) (.+?) HTTP', line)
                if match:
                    ip, timestamp, method, path = match.groups()
                    
                    # 过滤掉正常的系统文件
                    if 'webapps' not in path.lower():
                        if ip not in webshell_attempts:
                            webshell_attempts[ip] = []
                        webshell_attempts[ip].append({
                            'time': timestamp,
                            'method': method,
                            'path': path,
                            'line': line.strip()
                        })
        
        # 找出访问多个webshell的可疑IP
        for ip, attempts in webshell_attempts.items():
            if len(attempts) >= 5:  # 至少5次webshell尝试
                print(f"\n日志: {log_file}")
                print(f"可疑IP: {ip} (共{len(attempts)}次webshell尝试)")
                print("详细记录:")
                for attempt in attempts[:15]:  # 只显示前15个
                    print(f"  [{attempt['time']}] {attempt['method']} {attempt['path']}")

print("\n" + "="*80)
print("分析完成")
print("="*80)
