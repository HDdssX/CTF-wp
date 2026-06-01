from Crypto.Util.number import *
from gmpy2 import *
from random import *
import string
k = randint(30, 40)
str = string.digits + string.ascii_letters + "_@"
flag = b"VIDAR{" + "".join([choice(str) for i in range(k)]).encode() + b"}"
p = getPrime(120)
q = getPrime(120)
n = p * q
e = 65537
m = bytes_to_long(flag)
c = pow(m, e, n)
print(f'c = {c}')
print(f'p = {p}')
print(f'q = {q}')

'''
c = 451420045234442273941376910979916645887835448913611695130061067762180161
p = 722243413239346736518453990676052563
q = 777452004761824304315754169245494387
'''