from Crypto.Util.number import *
import ast

def solve_flux():
    with open('f:/CTF/CTF-wp/hgame/2026/week1/Flux/flux/data.txt', 'r') as f:
        lines = f.readlines()
        data = ast.literal_eval(lines[0].strip())
        n = int(lines[1].strip())
    
    x1, x2, x3, x4 = data
    
    # x2 = (a*x1^2 + b*x1 + c) % n
    # x3 = (a*x2^2 + b*x2 + c) % n
    # x4 = (a*x3^2 + b*x3 + c) % n
    
    # Eliminate c:
    # x3 - x2 = a(x2^2 - x1^2) + b(x2 - x1)
    # x4 - x3 = a(x3^2 - x2^2) + b(x3 - x2)
    
    def inverse(num, mod):
        return pow(num, -1, mod)
    
    term1_lhs = (x3 - x2) * inverse(x2 - x1, n) % n
    term1_rhs_a = (x2 + x1) % n
    # term1_lhs = a * (x2+x1) + b
    
    term2_lhs = (x4 - x3) * inverse(x3 - x2, n) % n
    term2_rhs_a = (x3 + x2) % n
    # term2_lhs = a * (x3+x2) + b
    
    # term2_lhs - term1_lhs = a * (x3+x2 - x2 - x1) = a * (x3 - x1)
    
    a = (term2_lhs - term1_lhs) * inverse(x3 - x1, n) % n
    b = (term1_lhs - a * term1_rhs_a) % n
    c = (x2 - a * pow(x1, 2, n) - b * x1) % n
    
    print(f"Found a: {a}")
    print(f"Found b: {b}")
    print(f"Found c: {c}")
    
    # Verify
    assert (a * pow(x1, 2, n) + b * x1 + c) % n == x2
    assert (a * pow(x2, 2, n) + b * x2 + c) % n == x3
    
    # Now find x0 (h)
    # x1 = (a*h^2 + b*h + c) % n
    # a*h^2 + b*h + (c - x1) = 0 (mod n)
    
    # Solve quadratic: Ax^2 + Bx + C = 0
    A = a
    B = b
    C_const = (c - x1) % n
    
    # Discriminant delta = B^2 - 4AC
    delta = (B*B - 4*A*C_const) % n
    
    # Sqrt delta
    # n is prime (getPrime(260))
    from Crypto.Util.number import isPrime
    # print(isPrime(n)) # Assume it is
    
    def legendre(a, p):
        return pow(a, (p - 1) // 2, p)

    def tonelli(n, p):
        assert legendre(n, p) == 1, "not a square (mod p)"
        q = p - 1
        s = 0
        while q % 2 == 0:
            q //= 2
            s += 1
        if s == 1:
            return pow(n, (p + 1) // 4, p)
        for z in range(2, p):
            if legendre(z, p) == p - 1:
                c = pow(z, q, p)
                break
        r = pow(n, (q + 1) // 2, p)
        t = pow(n, q, p)
        m = s
        t2 = 0
        while (t - 1) % p != 0:
            t2 = (t * t) % p
            for i in range(1, m):
                if (t2 - 1) % p == 0:
                    break
                t2 = (t2 * t2) % p
            b = pow(c, 1 << (m - i - 1), p)
            r = (r * b) % p
            c = (b * b) % p
            t = (t * c) % p
            m = i
        return r

    try:
        sqrt_delta = tonelli(delta, n)
        
        inv_2a = inverse(2*A, n)
        h1 = (-B + sqrt_delta) * inv_2a % n
        h2 = (-B - sqrt_delta) * inv_2a % n
        
        print(f"Candidate h1: {h1}")
        print(f"Candidate h2: {h2}")
        
        return [h1, h2]
    except Exception as e:
        print(f"Error finding sqrts: {e}")
        return []

solve_flux()
