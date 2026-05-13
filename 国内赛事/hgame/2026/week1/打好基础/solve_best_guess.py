
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Valid Key Range: 127744 (1F300) to 127999 (1F3FF) approx.
MIN_KEY = 127700
MAX_KEY = 128000

result = ""
for i, c in enumerate(content):
    code = ord(c)
    candidates = []
    
    # Try all valid ascii
    for p_code in range(32, 127):
        k = code - p_code
        if MIN_KEY <= k <= MAX_KEY:
            candidates.append(chr(p_code))
    
    best = None
    # Filter priorities
    # Priority 1: hgame{} chars if known position? No.
    # Priority 2: lower case, digits, _, {, }
    p2 = [x for x in candidates if x.islower() or x.isdigit() or x in "_{}"]
    if len(p2) == 1:
        best = p2[0]
    elif len(p2) > 1:
        # Ambiguity
        best = "[" + "".join(p2) + "]"
    
    if not best:
        # Priority 3: any printable
        if len(candidates) == 1:
            best = candidates[0]
        elif len(candidates) > 1:
            best = "(" + "".join(candidates) + ")"
        else:
            best = "?"
            
    result += best

print(result)
