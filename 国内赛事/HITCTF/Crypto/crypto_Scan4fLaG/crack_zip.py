#!/usr/bin/env python3
import zipfile

# 可能的密码列表
passwords = [
    # 解密后的各种形式
    'E3uy3g_b4kz_UUL_JGR_2025',
    'X3nr3z_u4ds_NNE_CZK_2025',
    'Q3gk3s_n4wl_GGX_VSD_2025',
    'WDNucjN6X3U0ZHNfTk5FX0NaS18yMDI1',
    'E3uy3g_b4kz_00L_JGR_2025',
    # 题目相关
    'Scan4fLaG',
    'HITCTF',
    '2025',
    'hint',
    'crypto',
    'fLaG',
    # 部分字符串
    'E3uy3g',
    'b4kz',
    'UUL',
    'JGR',
    'Eeuyeg_bakz_UUL_JGR_2025',
    # 其他ROT变体
    'Eluylg_bhkz_UUL_JGR_2025',
]

z = zipfile.ZipFile('hidden.zip')
success = False

for pwd in passwords:
    try:
        print(f"尝试密码: {pwd}", end=' ')
        z.extractall(pwd=pwd.encode())
        print(f"✓ 成功！")
        print(f"\n密码是: {pwd}")
        
        # 读取文件内容
        with open('fLaG', 'rb') as f:
            content = f.read()
            print(f"\n文件内容 (hex):\n{content.hex()}")
            try:
                print(f"\n文件内容 (text):\n{content.decode()}")
            except:
                pass
        success = True
        break
    except RuntimeError as e:
        print(f"✗")
        continue
    except Exception as e:
        print(f"✗ 错误: {e}")
        continue

if not success:
    print("\n所有密码都失败了，可能需要暴力破解或其他方法")
