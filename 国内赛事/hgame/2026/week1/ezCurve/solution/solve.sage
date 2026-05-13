import json
from sage.all import *

def solve():
    print("Loading data...")
    with open('solution/data.json', 'r') as f:
        data = json.load(f)
        
    p = int(data['p'])
    a = int(data['a'])
    b = int(data['b'])
    Rx = int(data['Rx'])
    Ry = int(data['Ry'])
    samples = {int(k): int(v) for k, v in data['samples'].items()}
    
    if 0 not in samples:
        print("Error: v0 (t=0) is missing")
        return

    v0 = samples[0]
    
    R = EllipticCurve(GF(p), [a, b])(Rx, Ry)
    
    # We use pairs (k, -k).
    pairs = []
    keys = sorted(samples.keys())
    for k in keys:
        if k <= 0: continue
        if -k in samples:
            pairs.append(k)
            
    print(f"Found {len(pairs)} pairs")
    
    # Define polynomial ring
    # We'll use resultants to eliminate e0.
    # Variables: e0, d1, d2 (we pick 2 pairs)
    
    # Pick 2 pairs
    pair_indices = [0, 1] 
    k1 = pairs[0]
    k2 = pairs[1]
    
    # Construct F1(e0, d1) and F2(e0, d2)
    PR = PolynomialRing(Zmod(p), names=['e0', 'd1', 'd2'])
    e0, d1, d2 = PR.gens()
    
    def get_poly(k, delta_var):
        v_plus = samples[k]
        v_minus = samples[-k]
        P_kR = k * R
        x_kR = int(P_kR[0])
        
        Vk = v_plus + v_minus
        Dk = v0 - x_kR
        
        term1 = v0 + e0 + x_kR
        term2 = a + (v0 + e0) * x_kR
        rhs = 2 * term1 * term2 + 4 * b
        lhs = (Vk + delta_var) * (Dk + e0)**2
        return lhs - rhs

    f1 = get_poly(k1, d1)
    f2 = get_poly(k2, d2)
    
    print("Computing resultant to eliminate e0...")
    # Resultant of f1, f2 with respect to e0
    # Note: Sage resultant on multivariate polynomial ring
    # We need to treat them as polynomials in e0 with coefficients in other variables
    PR2 = PolynomialRing(PR.base_ring(), names=['d1', 'd2'])
    
    # Manual resultant maybe better to control degree?
    # Or just use built-in
    # Convert to univariate in e0 over ring of d1,d2
    R_d = PolynomialRing(Zmod(p), names=['d1', 'd2'])
    R_e0 = PolynomialRing(R_d, name='e0')
    
    f1_r = R_e0(str(f1)) # quick conversion via string or coeff mapping
    f2_r = R_e0(str(f2))
    
    res = f1_r.resultant(f2_r)
    
    # res is in R_d (d1, d2)
    #Find small roots
    print("Finding small roots for resultant...")
    
    # Bounds
    B = 2**164
    
    # small_roots on multivariate
    # We need to lift to integers for small_roots
    res_z = res.change_ring(ZZ)
    
    try:
        roots = res_z.small_roots(epsilon=0.03, X=B)
        print(f"Roots found: {roots}")
        
        for root in roots:
            d1_val = root[0]
            d2_val = root[1]
            print(f"Candidate errors: d1={d1_val}, d2={d2_val}")
            
            # Now recover e0
            # Substitute d1 into f1 and solve for e0
            # f1(e0, d1_val) = 0
            
            R_uni = PolynomialRing(Zmod(p), name='x')
            f1_sub = f1(d1=d1_val, d2=d2_val, e0=R_uni.gen())
            
            roots_e0 = f1_sub.roots()
            print(f"Roots for e0: {roots_e0}")
            
            for r_e0, mult in roots_e0:
                e0_cand = int(r_e0)
                # Verify bounds
                if abs(e0_cand) < 2**163:
                    print(f"Found e0: {e0_cand}")
                    print(f"Calculated P[0] = {v0 + e0_cand}")
                    return
                # Handle large positive residue as negative
                if abs(e0_cand - p) < 2**163:
                     e0_cand = e0_cand - p
                     print(f"Found e0: {e0_cand}")
                     print(f"Calculated P[0] = {v0 + e0_cand}")
                     return

    except Exception as e:
        print(f"Optimization failed or no roots found: {e}")
        # Fallback: maybe try different pairs?
        
if __name__ == "__main__":
    solve()
