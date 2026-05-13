
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

offset = 128050 - 104 # 127946

decoded_chars = []
for i, c in enumerate(content):
    val = ord(c) - offset
    # Try to see if it is in readable ascii range
    if 32 <= val <= 126:
        decoded_chars.append(chr(val))
    else:
        decoded_chars.append(f"[{val}]")

print("".join(decoded_chars))
