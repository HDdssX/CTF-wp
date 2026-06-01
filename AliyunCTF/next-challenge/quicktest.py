import requests

resp = requests.post(
    'http://223.6.249.127:52324/', 
    headers={
        'Next-Action': '4075e5f81d75f63fee7dc5d3c1f87c166bc7fb5b3d', 
        'Content-Type': 'text/plain'
    }, 
    data='["test"]'
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
