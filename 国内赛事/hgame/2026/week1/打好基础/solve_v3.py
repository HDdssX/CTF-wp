
with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

unique = sorted(list(set(content)))
indices = [unique.index(c) for c in content[:5]]
print(f"Indices: {indices}")

# Compare with my calculated values for "hgam"
# Calculated: 33, 46, 83, 52, 71
expected = [33, 46, 83, 52, 71]
print(f"Expected: {expected}")
print(f"Match: {indices == expected}")
