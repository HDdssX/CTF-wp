"""
CTF Challenge: myRSA 解题脚本

题目分析:
1. p = pp² + 3*pp + 3
2. q = pp² + 5*pp + 7  
3. n = p * q * r
4. oracle(x): 返回 x 模 n 的平方根 (如果存在)

关键攻击思路:
=============
oracle 返回 ans 满足 ans² ≡ x (mod n)

由于 n = p*q*r 有多个因子，对于同一个 x，存在多个不同的平方根。
如果 oracle 返回的平方根 ans 与我们自己计算的某个平方根 ans' 不同，
那么 gcd(ans - ans', n) 可能给出 n 的因子！

但更直接的方法: 
由于 p, q 的特殊形式，直接爆破 pp 即可
"""

from Crypto.Util.number import long_to_bytes, isPrime
from math import gcd


def solve_by_bruteforce(n, c):
    """
    方法1: 直接爆破 pp 来分解 n
    适用于 pp 不太大的情况
    """
    print("[*] 开始爆破 pp 值...")
    
    for pp_val in range(1, 10**8):
        p_val = pp_val**2 + 3*pp_val + 3
        q_val = pp_val**2 + 5*pp_val + 7
        pq = p_val * q_val
        
        if pq > n:
            print(f"[!] pq > n at pp = {pp_val}, 停止搜索")
            break
        
        if n % pq == 0:
            r_val = n // pq
            if r_val > 1 and isPrime(r_val) and isPrime(p_val) and isPrime(q_val):
                print(f"[+] Found! pp = {pp_val}")
                print(f"[+] p = {p_val}")
                print(f"[+] q = {q_val}")  
                print(f"[+] r = {r_val}")
                
                return decrypt(n, c, p_val, q_val, r_val)
        
        if pp_val % 500000 == 0:
            print(f"[*] Progress: pp = {pp_val}")
    
    print("[-] 爆破失败")
    return None


def solve_by_oracle(n, c, oracle_results):
    """
    方法2: 利用 oracle 返回值分解 n
    
    oracle_results: dict {x: ans} 
    如果 oracle(x) = "🤐", 则 ans = None
    """
    print("[*] 尝试利用 oracle 结果分解 n...")
    
    for x, ans in oracle_results.items():
        if ans is None:
            continue
            
        # ans² ≡ x (mod n)
        # 尝试找另一个平方根 ans'，使得 gcd(ans - ans', n) 是非平凡因子
        
        # 由于 n 有3个因子，x 有 8 个平方根 (如果都是二次剩余)
        # 我们知道一个平方根 ans，另一个是 n - ans
        
        # 尝试: gcd(ans^2 - x, n) 应该 = n (如果计算正确)
        # 但 gcd(ans, n) 可能泄露因子
        
        g = gcd(ans, n)
        if 1 < g < n:
            print(f"[+] 通过 gcd(oracle({x}), n) 找到因子: {g}")
            # 继续分解
            
    print("[-] Oracle 方法未能找到因子")
    return None


def solve_by_polynomial_gcd(n):
    """
    方法3: 利用 p, q 的多项式关系
    
    设 f(x) = x² + 3x + 3 - p = 0 (mod p) 当 x = pp
    设 g(x) = x² + 5x + 7 - q = 0 (mod q) 当 x = pp
    
    我们知道 n = p*q*r，可以在模 n 下做多项式 GCD
    """
    # 这个方法比较复杂，暂时使用爆破方法
    pass


def decrypt(n, c, p, q, r):
    """
    使用分解后的因子解密
    """
    phi = (p - 1) * (q - 1) * (r - 1)
    e = 65537
    d = pow(e, -1, phi)  # Python 3.8+ 支持模逆元
    m = pow(c, d, n)
    flag = long_to_bytes(int(m))
    
    print(f"\n[+] Flag: {flag}")
    return flag


def factor_using_relation(n):
    """
    利用 p, q 的关系: q - p = 2(pp + 2)
    
    设 k = q - p = 2pp + 4
    则 pp = (k - 4) / 2
    
    p = pp² + 3pp + 3
    q = p + k
    
    n = p * q * r = p * (p + k) * r
    
    对于不同的 k，检查 n % (p * (p+k)) == 0
    """
    print("[*] 利用 p, q 的关系进行分解...")
    
    # k = 2(pp + 2), pp >= 1, 所以 k >= 6, k 是偶数
    for k in range(6, 10**8, 2):
        pp = (k - 4) // 2
        p = pp**2 + 3*pp + 3
        q = pp**2 + 5*pp + 7
        
        assert q - p == k  # 验证关系
        
        pq = p * q
        if pq > n:
            break
            
        if n % pq == 0:
            r = n // pq
            if isPrime(p) and isPrime(q) and isPrime(r):
                print(f"[+] Found! pp = {pp}, k = {k}")
                return p, q, r
                
        if pp % 500000 == 0:
            print(f"[*] Progress: pp = {pp}")
    
    return None


# ==================== 主程序 ====================
if __name__ == "__main__":
    # 从远程获取的 n 和 c 值
    n = 320463398964822335046388577512598439169912412662663009494347432623554394203670803089065987779128504277420596228400774827331351610218400792101575854579340551173392220602541203502751384517150046009415263351743602382113258267162420601780488075168957353780597674878144369327869964465070900596283281886408183175554478081038993938477659926361457163384937565266894839330377063520304463379213493662243218514993889537829099698656597997161855278297938355255410088350528543369288722795261835727770017939399082258134647208444374973242138569356754462210049877096486232693547694891534331539434254781094641373606991238019101335437
    c = 80140760654462267017719473677495407945806989083076205994692983838456863987736401342704400427420046369099889997909749061368480651101102957366243793278412775082041015336890704820532767466703387606369163429880159007880606865852075573350086563934479736264492605192640115037085361523151744341819385022516548746015224651520456608321954049996777342018093920514055242719341522462068436565236490888149658105227332969276825894486219704822623333003530407496629970767624179771340249861283624439879882322915841180645525481839850978628245753026288794265196088121281665948230166544293876326256961232824906231788653397049122767633
    
    # 如果有 oracle 交互结果，填入这里
    oracle_results = {}
    
    # 使用爆破方法解密
    result = solve_by_bruteforce(n, c)
