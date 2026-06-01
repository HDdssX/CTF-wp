from Crypto.Util.number import isPrime

keys = [860533, 292253282673537609320, 882549093032243261032]

for k in keys:
    print(f"Key: {k}")
    print(f"Bit length: {k.bit_length()}")
    print(f"Is Prime: {isPrime(k)}")
