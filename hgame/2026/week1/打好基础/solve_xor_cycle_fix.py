
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Derive keys based on hgame{
expected = "hgame{"
keys = []
for i, char in enumerate(expected):
    c_val = ord(content[i])
    p_val = ord(char)
    key = c_val ^ p_val
    keys.append(key)

print(f"Derived Keys: {[hex(k) for k in keys]}")

result = ""
for i, c in enumerate(content):
    k = keys[i % len(keys)]
    p = ord(c) ^ k
    if 32 <= p <= 126:
        result += chr(p)
    else:
        # result += "?"
        # Print hex if not ascii
        result += f"\\x{p:02x}"

print(result)
