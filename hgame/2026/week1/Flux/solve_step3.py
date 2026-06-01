
def shash(value, key):
    length = len(value)
    if length == 0: return 0
    mask = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    x = (ord(value[0]) << 7) & mask
    for c in value:
        x = (key * x) & mask ^ ord(c)
    x ^= length & mask
    return x

keys = [860533, 292253282673537609320, 882549093032243261032]
magic_word = "I get the key now!"

for k in keys:
    res = shash(magic_word, k)
    flag = "VIDAR{" + hex(res)[2:] + "}"
    print(f"Key: {k}")
    print(f"Flag: {flag}")
