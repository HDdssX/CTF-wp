from Crypto.Util.number import inverse, long_to_bytes
import string

c = 451420045234442273941376910979916645887835448913611695130061067762180161
p = 722243413239346736518453990676052563
q = 777452004761824304315754169245494387
e = 65537

n = p*q
phi = (p-1)*(q-1)
d = inverse(e, phi)
r = pow(c, d, n)

alphabet = string.digits + string.ascii_letters + "_@"

# 64进制（低位在前）取 40 个字符
val = r
chars = []
for _ in range(40):
    val, rem = divmod(val, 64)
    chars.append(alphabet[rem])

flag = "VIDAR{" + "".join(chars) + "}"
print(flag)