
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# Derived keys from "hgame{"
# Key = Cipher - Plain
keys = [127946, 127990, 127952, 127956, 127995, 127987]

print(f"Key emojis: {[chr(k) for k in keys]}")

found_counts = {k: 0 for k in keys}
for c in content:
    if ord(c) in keys:
        found_counts[ord(c)] += 1

print(f"Key presence in file: {found_counts}")

# Try to find Key[6]
# Cipher[6] = '👌' (128076).
# Key[6] = Cipher[6] - Plain[6].
# The previous attempt with repeating key produced '\x82' -> 130.
# 128076 - 127946 = 130.
# If Plain[6] is 'e' (101)?
# Key = 128076 - 101 = 127975 (`U+1F3E7` 🏧 ATM Sign).
# If Plain[6] is 'm' (109)?
# Key = 128076 - 109 = 127967 (`U+1F3DF` 🏟 Stadium).
# If Plain[6] is 'o' (111)?
# Key = 128076 - 111 = 127965 (`U+1F3DD` 🏝 Desert Island).
# If Plain[6] is 'j' (106)?
# Key = 128076 - 106 = 127970 (`U+1F3E2` 🏢 Office Building).
# If Plain[6] is 'i' (105)?
# Key = 128076 - 105 = 127971 (`U+1F3E3` 🏣 Japanese Post Office).

# Let's see the theme:
# Swimmer, Circus, Popcorn, Mountain, Skin, White Flag.
# Places/Activites?
# ATM, Stadium, Desert Island, Office...

# Let's brute force all chars and see if the resulting Key is a valid Emoji.
def is_emoji(n):
    return 0x1F300 <= n <= 0x1FAFF # Broad range

candidates = []
for ch_code in range(32, 127):
    k_val = 128076 - ch_code
    if is_emoji(k_val):
        candidates.append((chr(ch_code), k_val, chr(k_val)))

print("Candidates for Plain[6] and Key[6]:")
for c, kv, kchar in candidates:
    print(f"'{c}' -> {hex(kv)} {kchar}")

# Search for pattern in keys
