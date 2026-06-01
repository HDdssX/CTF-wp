import hashlib

d = 0xd35fe9a03a2162fd5441bb19346d95fdf885849bf61cd8f1d3c3901ee4af2eb2
k = 0xbfd1d9e5107448530d17e4de347c662cafded6afe33558f14737e5dc9c397b25

d_hex = hex(d)[2:]
d_HEX = d_hex.upper()
d_dec = str(d)
d_bytes = d.to_bytes(32,'big')
k_hex = hex(k)[2:]
k_bytes = k.to_bytes(32,'big')

# Various MD5 candidates
print('=== MD5 candidates ===')
print('md5(d_hex_lower):', hashlib.md5(d_hex.encode()).hexdigest())
print('md5(d_hex_upper):', hashlib.md5(d_HEX.encode()).hexdigest())
print('md5(d_dec):', hashlib.md5(d_dec.encode()).hexdigest())
print('md5(d_bytes):', hashlib.md5(d_bytes).hexdigest())
print('md5(0x+hex):', hashlib.md5(('0x'+d_hex).encode()).hexdigest())
print('md5(k_hex):', hashlib.md5(k_hex.encode()).hexdigest())
print('md5(k_bytes):', hashlib.md5(k_bytes).hexdigest())
print('md5(k_dec):', hashlib.md5(str(k).encode()).hexdigest())

print()
print('=== SHA256[:32] ===')
print('sha256(d_hex)[:32]:', hashlib.sha256(d_hex.encode()).hexdigest()[:32])
print('sha256(d_bytes)[:32]:', hashlib.sha256(d_bytes).hexdigest()[:32])
print('sha256(d_dec)[:32]:', hashlib.sha256(d_dec.encode()).hexdigest()[:32])

print()
print('=== Slices ===')
print('d_hex first 32:', d_hex[:32])
print('d_hex last  32:', d_hex[-32:])
print('k_hex first 32:', k_hex[:32])
print('k_hex last  32:', k_hex[-32:])

# combined
combined = d ^ k
print('d xor k:', hex(combined)[2:])
print('(d xor k)[:32]:', hex(combined)[2:][:32])
print('(d xor k)[-32:]:', hex(combined)[2:][-32:])
