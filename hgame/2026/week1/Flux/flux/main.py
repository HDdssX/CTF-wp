from Crypto.Util.number import *
import random
from secret import key

class Flux:
    def __init__(self, n, x):
        self.n = n
        self.a = random.randint(1, n-1)
        self.b = random.randint(1, n-1)
        self.c = random.randint(1, n-1)
        self.x = x
    
    def next(self):
        self.x = (self.a * self.x ** 2 + self.b * self.x + self.c) % self.n
        return self.x

def shash(value: str,key: int) -> int:
    length = len(value)

    if length == 0:
        return 0
    mask = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    x = (ord(value[0]) << 7) & mask
    for c in value:
        x = (key * x) & mask ^ ord(c)

    x ^= length & mask

    return x

assert key.bit_length() < 70
value = "Welcome to HGAME 2026!"
h = shash(value, key)

n = getPrime(260)
flux = Flux(n, h)
data = [flux.next() for _ in range(4)]

with open('data.txt', 'w') as f:
    f.write(f"{data}\n")
    f.write(f"{n}\n")

magic_word = "I get the key now!"
flag = "VIDAR{" + hex(shash(magic_word, key))[2:] + "}"
print(flag)