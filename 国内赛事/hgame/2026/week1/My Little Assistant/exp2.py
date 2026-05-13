import requests
import json

url = "http://cloud-middle.hgame.vidar.club:30411/execute_tool"
headers = {
    "Content-Type": "application/json"
}
# Try py_request
data = {
    "name": "py_request",
    "arguments": {
        "url": "http://example.com"
    }
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
