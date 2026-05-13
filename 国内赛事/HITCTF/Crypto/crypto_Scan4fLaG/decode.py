import base64

encoded = "WDNucjN6X3U0ZHNfTk5FX0NaS18yMDI1"
decoded = base64.b64decode(encoded).decode()
print("1. Base64解码:", decoded)

# ROT7
result = []
for char in decoded:
    if 'a' <= char <= 'z':
        result.append(chr((ord(char) - ord('a') + 7) % 26 + ord('a')))
    elif 'A' <= char <= 'Z':
        result.append(chr((ord(char) - ord('A') + 7) % 26 + ord('A')))
    else:
        result.append(char)
rot7 = ''.join(result)
print("2. ROT7:", rot7)

# Leetspeak 解码
leet_map = {
    '3': 'e',
    '4': 'a', 
    '0': 'o',
    '1': 'i',
    '7': 't',
    '5': 's'
}

final = []
for char in rot7:
    if char in leet_map:
        final.append(leet_map[char])
    else:
        final.append(char)
        
final_result = ''.join(final)
print("3. Leetspeak解码:", final_result)
print("\nFlag: HITCTF{" + final_result + "}")
