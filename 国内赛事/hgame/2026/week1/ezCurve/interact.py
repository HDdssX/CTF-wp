from pwn import *
import json
import re

# Set up logging
context.log_level = 'info'

def solve():
    # Connect to server
    try:
        r = remote('cloud-big.hgame.vidar.club', 32400)
    except:
        print("Could not connect to server.")
        return

    # Receive parameters
    r.recvuntil(b'connection from')
    
    # helper to read numbers
    def get_num():
        line = r.recvline().decode().strip()
        return int(line)

    # Read p, a, b
    # Server prints p, a, b, R randomly?
    # Code:
    # print(p, file = ostream)
    # print(a, file = ostream)
    # print(b, file = ostream)
    # print(R, file = ostream)
    
    # We need to parse R. R is a point. Sage prints it like (x : y : z) for projective or (x, y) for affine.
    # Usually affine for random_element().
    # Let's inspect raw output first to be sure about format.
    
    # To be safe, I'll read lines and parse.
    # But I can't restart connection easily if I mess up.
    # I'll just assume standard format.
    
    # Actually, R print format in sage:
    # (123123, 321321) usually.
    # Or (12312 : 12312 : 1) if projective.
    # Server uses: E.random_element().
    # Let's read 4 lines.
    
    line_p = r.recvline().decode().strip()
    line_a = r.recvline().decode().strip()
    line_b = r.recvline().decode().strip()
    line_R = r.recvline().decode().strip()
    
    print(f"[+] p = {line_p}")
    print(f"[+] a = {line_a}")
    print(f"[+] b = {line_b}")
    print(f"[+] R = {line_R}")

    p = int(line_p)
    a = int(line_a)
    b = int(line_b)
    
    # Parse R
    # Simplify: remove '(', ')', split by ','
    clean_R = line_R.replace('(', '').replace(')', '').replace(' ', '')
    parts = clean_R.split(',')
    rx = int(parts[0])
    ry = int(parts[1])
    # if there is a 3rd part, check if it's 1. Usually is.
    
    queries = []
    # Plan: 
    # t=0
    # t=1, t=-1
    # ...
    # t=14, t=-14
    
    targets = [0]
    for i in range(1, 15):
        targets.append(i)
        targets.append(-i)
        
    responses = {}
    
    for t_val in targets:
        r.recvuntil(b'> ')
        r.sendline(b'1') # get x
        r.recvuntil(b't> t = ')
        r.sendline(str(t_val).encode())
        ans_line = r.recvline().decode().strip()
        val = int(ans_line)
        responses[t_val] = val
        print(f"t={t_val} -> {val}")

    print("[+] collected samples")
    
    # Prepare data for solver
    data = {
        "p": str(p),
        "a": str(a),
        "b": str(b),
        "Rx": str(rx),
        "Ry": str(ry),
        "samples": responses
    }
    
    with open("solution/data.json", "w") as f:
        json.dump(data, f, indent=4)
        
    print("[+] data.json saved.")
    print("Please run 'sage solve.sage' in this directory.")
    
    solution_x = input("Enter the calculated x coordinate of P: ")
    
    # Send check
    r.recvuntil(b'> ')
    r.sendline(b'2') # check x
    r.sendline(solution_x.encode())
    
    result = r.recvall(timeout=2).decode().strip()
    print(result)

if __name__ == "__main__":
    solve()
