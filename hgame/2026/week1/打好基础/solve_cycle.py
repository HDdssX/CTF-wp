
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Keys derived from hgame{
keys = [127946, 127990, 127952, 127956, 127995, 127987]

result = ""
for i, c in enumerate(content):
    k = keys[i % len(keys)]
    p = ord(c) - k
    # Check bounds
    if 32 <= p <= 126:
        result += chr(p)
    else:
        result += "?" # or chr(p) if possible

print(result)
