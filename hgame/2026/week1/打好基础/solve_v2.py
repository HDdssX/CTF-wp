
import collections
import struct

with open('stuck_out_tongue_.txt', 'r', encoding='utf-8') as f:
    content = f.read().strip()

print(f"Count: {len(content)}")
unique_chars = sorted(list(set(content)))
print(f"Unique characters count: {len(unique_chars)}")

ords = [ord(c) for c in unique_chars]
print(f"Min ord: {min(ords)}, Max ord: {max(ords)}")
print(f"Range: {max(ords) - min(ords)}")

# Try Base85 decoding assuming the sorted unique chars form the alphabet 0-84
indices = [unique_chars.index(c) for c in content]

# Base85 takes 5 chars -> 4 bytes
# Check if total length is multiple of 5
print(f"Indices length: {len(indices)}")
if len(indices) % 5 != 0:
    print(f"Warning: Length {len(indices)} is not a multiple of 5. Base85 usually requires padding or handles the last block differently.")

# Decode
decoded_bytes = bytearray()
for i in range(0, len(indices), 5):
    chunk = indices[i:i+5]
    if len(chunk) < 5:
        # Pad with the last char in unique_chars (value 84)?
        # Standard Ascii85 pads with 'u' (84)
        padding = 5 - len(chunk)
        chunk = chunk + [84] * padding
        val = 0
        for idx in chunk:
            val = val * 85 + idx
        try:
             # For the last chunk, we keep only (len(chunk_orig)-1) bytes? No, usually length-1
            b = val.to_bytes(4, 'big')
            decoded_bytes.extend(b[:5-padding-1]) # Approximation
        except Exception as e:
            print(f"Error converting last chunk {chunk}: {e}")
        continue
    
    val = 0
    for idx in chunk:
        val = val * 85 + idx
    
    try:
        b = val.to_bytes(4, 'big')
        decoded_bytes.extend(b)
    except Exception as e:
        print(f"Error converting chunk {chunk} to bytes: {e}")

#print(f"Decoded bytes: {decoded_bytes}")
try:
    print(f"Decoded string (utf8): {decoded_bytes.decode('utf-8', errors='replace')}")
except:
    pass
print(f"Decoded string (ascii): {decoded_bytes.decode('ascii', errors='replace')}")
