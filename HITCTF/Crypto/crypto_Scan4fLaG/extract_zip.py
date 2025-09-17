#!/usr/bin/env python3
# 从PNG图片中提取隐藏的ZIP文件

with open('hint.png', 'rb') as f:
    data = f.read()

# 查找ZIP文件的魔术头 PK (0x504B)
zip_start = data.find(b'PK')

if zip_start != -1:
    print(f"找到ZIP文件，起始位置: 0x{zip_start:x}")
    
    # 提取ZIP数据
    zip_data = data[zip_start:]
    
    # 保存为ZIP文件
    with open('hidden.zip', 'wb') as f:
        f.write(zip_data)
    
    print(f"已提取 {len(zip_data)} 字节到 hidden.zip")
else:
    print("未找到ZIP文件")
