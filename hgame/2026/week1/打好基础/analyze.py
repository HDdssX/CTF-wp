
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

emojis = list(content)
print(f"Count: {len(emojis)}")
values = [ord(c) for c in emojis]
print(f"First 10 values: {values[:10]}")

# Guessing 'h' 'g' 'a' 'm' 'e'
expected = [ord(c) for c in "hgame"]
print(f"Expected start bytes: {expected}")
print(f"First 5 emojis: {[hex(v) for v in values[:5]]}")

# Check differences
for i in range(len(expected)):
    print(f"Emoji {i} ({emojis[i]}): {values[i]} - Expected {expected[i]} = {values[i] - expected[i]}")

# Frequencies
from collections import Counter
c = Counter(values)
print(f"Unique emojis: {len(c)}")
print(f"Most common: {c.most_common(5)}")
