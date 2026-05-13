from bottle import template
from flask import stream_template_string
BLACKLIST = ["b","c","d","e","h","i","j","k","m","n","o","p","q","r","s","t","u","v","w","x","y","z","%",";",",","<",">",":","?"]

def contains_blacklist(content):
    """检查内容是否包含黑名单中的关键词（不区分大小写）"""
    content = content.lower()
    return any(black_word in content for black_word in BLACKLIST)

content = """{{().__class__}}"""
if contains_blacklist(content):
    print("文件内容包含不允许的关键词")
print(template(content))
print(stream_template_string(content))
