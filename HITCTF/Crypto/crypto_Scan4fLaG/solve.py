import base64

encoded = "WDNucjN6X3U0ZHNfTk5FX0NaS18yMDI1"
decoded = base64.b64decode(encoded).decode()
print("Base64解码:", decoded)

print("\n尝试所有Caesar/ROT偏移:")
for shift in range(26):
    result = []
    for char in decoded:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(char)
    result_str = ''.join(result)
    print(f"ROT{shift}: {result_str}")
    
print("\nFlag格式: HITCTF{...}")
