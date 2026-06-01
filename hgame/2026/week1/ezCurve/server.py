from Crypto.Util.number import *
import socketserver
import logging
import io
import os
from sage.all import *

with open('flag.txt', 'rb') as f:
    flag = f.read()

HOST = '0.0.0.0'
PORT = 10000

menu = """1. get x
2. check x
> """

class Curve(socketserver.StreamRequestHandler):
    def handle(self):
        global istream, ostream

        logging.info(f"connection from {self.client_address}")
        istream = io.TextIOWrapper(self.rfile, encoding="UTF-8")
        ostream = io.TextIOWrapper(self.wfile, encoding="UTF-8", write_through=True)
        
        p = getPrime(1024)
        a = getPrime(200)
        b = getPrime(200)
        E = EllipticCurve(GF(p), [a, b])
        R = E.random_element()
        P = E.random_element()

        print(p, file = ostream)
        print(a, file = ostream)
        print(b, file = ostream)
        print(R, file = ostream)

        for i in range(30):
            print(menu, file = ostream)
            choice = int(istream.readline().strip())
            if choice == 1:
                print("t> t = ", end = "", file = ostream)
                t = int(istream.readline().strip())
                O = P + t * R
                print(int(O[0] - getPrime(163)), file = ostream)
            elif choice == 2:
                ans = int(istream.readline().strip())
                if ans == P[0]:
                    print(flag, file = ostream)
                else:
                    print("error", file = ostream)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with socketserver.TCPServer((HOST, PORT), Curve) as server:
        logging.info(f"listening on {HOST}:{PORT}")
        server.serve_forever()

        
