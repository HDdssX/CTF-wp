import re

print("=== 6月21日18:00-23:59之间的所有活动 ===\n")

suspicious_ips = {}

with open('ex170621.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        # 匹配6月21日18:00到23:59之间的请求
        if re.search(r'21/Jun/2017:(1[8-9]|2[0-3]):', line):
            # 提取IP地址
            ip_match = re.match(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                ip = ip_match.group(1)
                # 查找可疑行为: POST请求, webshell尝试, 上传相关
                if 'POST' in line or '.php' in line or '.jsp' in line or '.asp' in line or 'upload' in line.lower() or 'multipart' in line.lower():
                    if ip not in suspicious_ips:
                        suspicious_ips[ip] = []
                    suspicious_ips[ip].append(line.strip())

print(f"发现 {len(suspicious_ips)} 个可疑IP\n")

for ip, requests in suspicious_ips.items():
    print(f"\n=== IP: {ip} ({len(requests)}条记录) ===")
    for req in requests[:10]:  # 只显示前10条
        print(req)
    if len(requests) > 10:
        print(f"... 还有 {len(requests)-10} 条记录")
