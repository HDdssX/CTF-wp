
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Derived keys from "hgame{"
keys = [127946, 127990, 127952, 127956, 127995, 127987]

decoded = []
for i, c in enumerate(content):
    k = keys[i % len(keys)]
    val = ord(c) - k
    decoded.append(val)

# Convert to string if possible
output = ""
for v in decoded:
    if 32 <= v <= 126:
        output += chr(v)
    else:
        output += f"\\x{v:02x}"

print(output)
