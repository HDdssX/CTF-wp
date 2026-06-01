import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url_base = "https://1de75a25-ddec-46aa-87f7-5dea6f47690d.challenge.ctf.show"

def list_artifacts(path="templates"):
    try:
        r = requests.get(f"{url_base}/api/v1/artifacts", params={"path": path}, verify=False)
        print(f"Path: {path}")
        print(r.text)
    except Exception as e:
        print(e)

list_artifacts("/app")
