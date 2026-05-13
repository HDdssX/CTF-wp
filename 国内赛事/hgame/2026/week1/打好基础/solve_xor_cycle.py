
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Keys derived from hgame{ using XOR
keys = [128022, 128062, 128114, 128044, 128061, 128005]

result = ""
for i, c in enumerate(content):
    k = keys[i % len(keys)]
    p = ord(c) ^ k
    if 32 <= p <= 126:
        result += chr(p)
    else:
        result += "?"

print(result)
