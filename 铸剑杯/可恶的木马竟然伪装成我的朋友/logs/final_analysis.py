import re

# 搜索最终答案: 综合分析
# 1. 找到3月28日晚上尝试webshell的IP和webshell列表
# 2. 找到6月21-22日可能上传木马的线索

print("=== 【线索3】2017年3月28日晚上IP 58.246.7.29尝试访问的webshell ===\n")

webshells = []
with open('ex170328.log', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '58.246.7.29' in line and re.search(r'28/Mar/2017:22:', line) and 'POST' in line:
            # 提取文件名
            match = re.search(r'POST /([a-zA-Z0-9_\.]+\.(php|asp|jsp|aspx)) ', line)
            if match:
                filename = match.group(1)
                if filename not in webshells:
                    webshells.append(filename)
                    print(f"{filename}")
                    print(line.strip())

print(f"\n按时间顺序排列的webshell: {'-'.join(webshells)}")

print("\n\n=== 【线索1和2】现在分析banner_home.jpg上传事件 ===\n")
print("根据分析:")
print("- 在6月21日19:56:35,banner_home.jpg文件大小还是50428字节")
print("- 在6月22日07:45:08,banner_home.jpg文件大小还是50428字节")  
print("- 在6月22日12:47:52,banner_home.jpg文件大小变成40920字节")
print("- 之后又恢复到50428字节")
print("\n这说明在6月22日上午7:45到12:47之间,有人上传/修改了banner_home.jpg")
print("但是没有找到明确的上传POST请求...")
print("\n让我检查6月20日-21日,因为题目说'某天晚上'...")
