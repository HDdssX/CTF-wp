
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Keys derived from hgame{
keys = [127946, 127990, 127952, 127956, 127995, 127987] # Swimmer, Circus, Popcorn, Mountain, Skin, Flag

# Also add the one we suspected from '}' at end? 127936 (Basketball)
keys.append(127936)

result = ""
for i, c in enumerate(content):
    code = ord(c)
    options = []
    for k in keys:
        p = code - k
        if 32 <= p <= 126:
            options.append(chr(p))
    
    if not options:
        result += "?"
    elif len(options) == 1:
        result += options[0]
    else:
        result += "[" + "".join(options) + "]"

print(result)
