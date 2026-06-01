#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424


def point_add(a, b):
    if a is None:
        return b
    if b is None:
        return a

    x1, y1 = a
    x2, y2 = b

    if x1 == x2 and (y1 + y2) % P == 0:
        return None

    if a == b:
        lam = (3 * x1 * x1) * pow((2 * y1) % P, -1, P) % P
    else:
        lam = ((y2 - y1) % P) * pow((x2 - x1) % P, -1, P) % P

    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def point_mul(k, point):
    result = None
    addend = point

    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1

    return result


def recover_private_key(challenge):
    r1 = challenge["signature1_r"]
    r2 = challenge["signature2_r"]
    s1 = challenge["signature1_s"]
    s2 = challenge["signature2_s"]

    if r1 != r2:
        raise ValueError("nonce was not reused: signature1_r != signature2_r")

    m1 = bytes.fromhex(challenge["message1"])
    m2 = bytes.fromhex(challenge["message2"])
    z1 = int.from_bytes(hashlib.sha256(m1).digest(), "big")
    z2 = int.from_bytes(hashlib.sha256(m2).digest(), "big")

    k = ((z1 - z2) * pow((s1 - s2) % N, -1, N)) % N
    d = ((s1 * k - z1) * pow(r1, -1, N)) % N
    return d, k


def verify_public_key(challenge, private_key):
    qx, qy = point_mul(private_key, (GX, GY))
    return (
        qx == challenge["public_key_x"] and qy == challenge["public_key_y"],
        qx,
        qy,
    )


def candidate_flags(private_key):
    key_hex = f"{private_key:064x}"
    key_raw = private_key.to_bytes(32, "big")
    key_dec = str(private_key)

    return {
        "hex_md5": hashlib.md5(key_hex.encode()).hexdigest(),
        "raw_md5": hashlib.md5(key_raw).hexdigest(),
        "dec_md5": hashlib.md5(key_dec.encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description="Recover an ECDSA private key from nonce reuse.")
    parser.add_argument(
        "challenge",
        nargs="?",
        default="otp_00/challenge.json",
        help="Path to challenge.json",
    )
    args = parser.parse_args()

    challenge_path = Path(args.challenge)
    challenge = json.loads(challenge_path.read_text(encoding="utf-8"))

    private_key, nonce = recover_private_key(challenge)
    ok, qx, qy = verify_public_key(challenge, private_key)
    flags = candidate_flags(private_key)

    print(f"challenge     : {challenge_path}")
    print(f"curve         : {challenge['curve']}")
    print(f"private_key   : {private_key:064x}")
    print(f"nonce_k       : {nonce}")
    print(f"pubkey_match  : {ok}")
    print(f"public_key_x  : {qx}")
    print(f"public_key_y  : {qy}")
    print()
    print("Most likely flag format:")
    print(f"flag{{ecdsa_nonce_reuse_{flags['hex_md5']}}}")
    print()
    print("Other common 32-hex variants:")
    print(f"raw-bytes md5 : flag{{ecdsa_nonce_reuse_{flags['raw_md5']}}}")
    print(f"decimal md5   : flag{{ecdsa_nonce_reuse_{flags['dec_md5']}}}")


if __name__ == "__main__":
    main()
