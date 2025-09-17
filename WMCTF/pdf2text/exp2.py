# python
def zpad10(n: int) -> bytes:
    return f"{n:010d}".encode("ascii")

# 原样保留的十六进制“文本”（不会转换为二进制）
HEX_TEXT = b"""1f8b 0808 e85e ee68 000b 622e 7069 636b
6c65 006b 6099 eace 0001 3d1c 49a5 9939
2599 79c5 537a 5852 2b52 93a7 4c9e d2a3
9d99 5b90 5f54 a290 5f6c 0dc4 7ac5 95c5
25a9 b91a 4aa9 c919 f90a 8686 860a 760a
fa69 10a0 a439 a575 4ad0 143d 00bc 372f
0b52 0000 00
"""

# 最小 PDF 片段
pdf_header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
obj2 = b"2 0 obj\n<< /Type /Pages /Count 0 >>\nendobj\n"

# 计算偏移（均相对于整个文件起始）
prefix_len = len(HEX_TEXT)
off_obj1 = prefix_len + len(pdf_header)
off_obj2 = off_obj1 + len(obj1)
startxref = prefix_len + len(pdf_header) + len(obj1) + len(obj2)

# 构造 xref / trailer / startxref
xref = (
    b"xref\n0 3\n"
    + zpad10(0) + b" 65535 f \n"
    + zpad10(off_obj1) + b" 00000 n \n"
    + zpad10(off_obj2) + b" 00000 n \n"
)
trailer = b"trailer\n<< /Size 3 /Root 1 0 R >>\n"
tail = xref + trailer + b"startxref\n" + str(startxref).encode("ascii") + b"\n%%EOF\n"

# 拼接并写出
poly = HEX_TEXT + pdf_header + obj1 + obj2 + tail
with open("poly_hex_text_plus_pdf.bin", "wb") as f:
    f.write(poly)

# 简单校验
hdr_pos = poly.find(b"%PDF-")
sx_pos = poly.rfind(b"startxref")
num_beg = sx_pos + len(b"startxref\n")
num_end = poly.find(b"\n", num_beg)
sx_val = int(poly[num_beg:num_end])
print("前缀长度:", prefix_len)
print("PDF header 位置:", hdr_pos)
print("startxref:", sx_val, "->", poly[sx_val:sx_val+4])
assert poly[sx_val:sx_val+4] == b"xref"
print("完成，输出文件: poly_hex_text_plus_pdf.bin")
