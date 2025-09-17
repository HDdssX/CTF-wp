import string
from twisted.words.protocols.jabber.xmpp_stringprep import nodeprep

def lower(username):
    username = nodeprep.prepare(username)
    return username

# 字典不全，因为使用的是dic[key]=value
dic = {}
alpha_dic = [i for i in string.ascii_letters]
for i in range(0xffff):
    tmp = b"\u" + hex(i)[2:].zfill(4).encode()
    try:
        low = lower(tmp.decode("unicode-escape"))
        original = tmp.decode("unicode-escape")
        if low in alpha_dic and original not in alpha_dic and len(low) == 1:
            dic[lower(tmp.decode("unicode-escape"))] = tmp.decode("unicode_escape")
    except Exception:
        pass

# print(dic)
payload = """print("ffff")"""
res = ""
for i in payload:
    if i in dic:
        res += dic[i]
    else:
        res += i
print(len(payload))
print(res)