import base64

# 从二维码扫描的Base64
encoded = "WDNucjN6X3U0ZHNfTk5FX0NaS18yMDI1"
step1 = base64.b64decode(encoded).decode()
print("Base64解码:", step1)

# 尝试反向ROT (ROT19 = -ROT7)
def rot(text, shift):
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(char)
    return ''.join(result)

# ROT19 (反向ROT7)
step2 = rot(step1, 19)
print("ROT19 (反向ROT7):", step2)

# ROT7 (正向)
step3 = rot(step1, 7)
print("ROT7:", step3)

print("\n分析 'Scan4fLaG' 题目名:")
print("4 = for/a")
print("如果flag格式是 E3uy3g_b4kz_00L_JGR_2025")
print("其中 UU 可能是 00 (字母O)")

# 尝试替换
modified = step3.replace('UUL', '00L').replace('JGR', 'JGR')
print("\n替换后:", modified)

print("\n可能的Flag:")
print(f"HITCTF{{{step3}}}")
print(f"或 HITCTF{{{step2}}}")
