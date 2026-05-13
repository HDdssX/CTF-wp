import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://1de75a25-ddec-46aa-87f7-5dea6f47690d.challenge.ctf.show/static/app.js"
response = requests.get(url, verify=False)
with open("f:\\CTF\\CTF-wp\\ctfshow\\2026CS\\SafeViewer\\app.js", "w", encoding="utf-8") as f:
    f.write(response.text)
print("Done")
