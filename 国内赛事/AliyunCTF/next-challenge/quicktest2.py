import requests

NEW_ACTION_ID = "401da4050210f37f7fa7a9507207e6ca489478998d"

resp = requests.post(
    'http://223.6.249.127:52324/', 
    headers={
        'Next-Action': NEW_ACTION_ID, 
        'Content-Type': 'text/plain'
    }, 
    data='["test"]'
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
