
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Key Range Estimate
MIN_KEY = 127900
MAX_KEY = 128000

result = []
for i, c in enumerate(content):
    code = ord(c)
    possibles = []
    # Key = Cipher - Plain
    # Plain = Cipher - Key
    # We want Plain in [32, 126]
    # So Key = Cipher - Plain
    # Min Key = Cipher - 126
    # Max Key = Cipher - 32
    
    start_k = code - 126
    end_k = code - 32
    
    # Intersection with Valid Key Range
    search_start = max(MIN_KEY, start_k)
    search_end = min(MAX_KEY, end_k)
    
    for k in range(search_start, search_end + 1):
        # We could filter K by "Is it a valid emoji?" but let's just use range for now
        p = code - k
        if 32 <= p <= 126:
            possibles.append(chr(p))
            
    if not possibles:
        result.append("?")
    elif len(possibles) == 1:
        result.append(possibles[0])
    else:
        # Heuristic: Prefer lowercase letters? Or try to look for common key reuse?
        # For now, print [options]
        result.append("[" + "".join(possibles) + "]")

print("".join(result))
