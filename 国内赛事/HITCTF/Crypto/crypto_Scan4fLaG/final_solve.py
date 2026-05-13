import base64

# 步骤1: Base64解码
encoded = "WDNucjN6X3U0ZHNfTk5FX0NaS18yMDI1"
decoded = base64.b64decode(encoded).decode()
print("步骤1 - Base64解码:", decoded)
# 结果: X3nr3z_u4ds_NNE_CZK_2025

# 步骤2: ROT7
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

rot7_result = rot(decoded, 7)
print("步骤2 - ROT7:", rot7_result)
# 结果: E3uy3g_b4kz_UUL_JGR_2025

# 步骤3: 1337 speak 转换
# 3 -> e, 4 -> a
leet_decode = rot7_result.replace('3', 'e').replace('4', 'a')
print("步骤3 - Leet解码:", leet_decode)
# 结果: Eeuyeg_bakz_UUL_JGR_2025

# 让我们看看是否应该先转leet再rot
print("\n尝试另一种顺序:")
# 先leet解码原始的
leet_first = decoded.replace('3', 'e').replace('4', 'a')
print("先Leet解码:", leet_first)
# Xenrez_uads_NNE_CZK_2025

rot7_second = rot(leet_first, 7)
print("再ROT7:", rot7_second)
# Eluylg_hbkz_UUL_JGR_2025

print("\n最终Flag: HITCTF{" + rot7_result + "}")
