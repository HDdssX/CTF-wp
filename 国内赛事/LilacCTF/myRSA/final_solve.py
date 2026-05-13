"""
最终解题脚本 - 利用已知数据
"""
from math import gcd
from Crypto.Util.number import long_to_bytes, isPrime

# 服务器返回的数据（已手动验证）
# n 是固定的，所以可以直接硬编码
n_str = """320463398964822335046388577512598439169912412662663009494347432623554394203670803089065987779128504277420596228400774827331351610218400792101575854579340551173392220602541203502751384517150046009415263351743602382113258267162420601780488075168957353780597674878144369327869964465070900596283281886408183175554478081038993938477659926361457163384937565266894839330377063520304463379213493662243218514993889537829099698656597997161855278297938355255410088350528543369288722795261835727770017939399082258134647208444374973242138569356754462210049877096486232693547694891534331539434254781094641373606991238019101335437"""

c_str = """80140760654462267017719473677495407945806989083076205994692983838456863987736401342704400427420046369099889997909749061368480651101102957366243793278412775082041015336890704820532767466703387606369163429880159007880606865852075573350086563934479736264492605192640115037085361523151744341819385022516548746015224651520456608321954049996777342018093920514055242719341522462068436565236490888149658105227332969276825894486219704822623333003530407496629970767624179771340249861283624439879882322915841180645525481839850978628245753026288794265196088121281665948230166544293876326256961232824906231788653397049122767633"""

n = int(n_str.replace('\n', '').replace(' ', ''))
c = int(c_str.replace('\n', '').replace(' ', ''))

print(f"n = {n}")
print(f"n bits = {n.bit_length()}")
print(f"c = {c}")
print(f"c bits = {c.bit_length()}")

# 尝试直接分解
# 根据题目，p = pp² + 3pp + 3, q = pp² + 5pp + 7
# n = p * q * r

# 方法: 使用 CRT + 多模约束加速
# 已知 pp mod 97 ∈ {4, 7, 14, 15, 19, 20, 35, 38, 41, 52, 55, 58, 73, 74, 78, 79, 86, 89, 94, 95, 96}

# 进一步约束: 检查 pp mod 83 和 pp mod 89

# 模 83 的二次剩余
qr_83 = set(pow(i, 2, 83) for i in range(1, 83))
# 模 89 的二次剩余  
qr_89 = set(pow(i, 2, 89) for i in range(1, 89))
# 模 97 的二次剩余
qr_97 = set(pow(i, 2, 97) for i in range(1, 97))

# 根据 oracle 结果:
# - 97 是公共二次剩余 (oracle 返回值)
# - 83, 89 不是公共二次剩余 (oracle 返回 🤐)

# 这意味着对于至少一个因子 (p, q 或 r)，83 不是二次剩余
# 同样，89 也不是

# 让我们利用 n mod small_prime 的约束
n_mod_83 = n % 83
n_mod_89 = n % 89
n_mod_97 = n % 97

print(f"\nn mod 83 = {n_mod_83}")
print(f"n mod 89 = {n_mod_89}")
print(f"n mod 97 = {n_mod_97}")

# 使用 CRT 组合多个模约束来加速搜索
# pp 需要满足:
# 1. (pp² + 3pp + 3) mod 97 ∈ QR(97)
# 2. (pp² + 5pp + 7) mod 97 ∈ QR(97)
# 3. 根据 n 的约束

# 计算满足条件的 pp mod (83*89*97)
from functools import reduce

def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = extended_gcd(b, a % b)
    return g, y, x - (a // b) * y

def crt_combine(remainders, moduli):
    """中国剩余定理"""
    M = reduce(lambda x, y: x * y, moduli)
    result = 0
    for r, m in zip(remainders, moduli):
        Mi = M // m
        _, inv, _ = extended_gcd(Mi, m)
        result += r * Mi * (inv % m)
    return result % M

# 生成所有有效的 pp mod 97 值 (基于 97 是 p, q 的 QR)
valid_pp_97 = []
for pp in range(97):
    p_mod = (pp*pp + 3*pp + 3) % 97
    q_mod = (pp*pp + 5*pp + 7) % 97
    if p_mod in qr_97 and q_mod in qr_97:
        valid_pp_97.append(pp)

print(f"\n有效的 pp mod 97: {valid_pp_97} ({len(valid_pp_97)} 个)")

# 对于 83: 至少 p 或 q 或 r 不是 QR
# 我们需要找到使得 p*q*r mod 83 = n mod 83 的组合

# 先计算所有可能的 (pp mod 83, pp mod 89, pp mod 97) 组合
# 然后用 CRT 合并

# 简化: 直接用 97 的约束，每隔 97 搜索
print("\n开始基于模 97 约束的搜索...")

def search_pp(max_pp=10**12):
    """搜索 pp"""
    for base in valid_pp_97:
        if base == 0:
            base = 97
        pp = base
        while pp < max_pp:
            p = pp*pp + 3*pp + 3
            q = pp*pp + 5*pp + 7
            pq = p * q
            
            if pq > n:
                # 对于当前 base，pp 已经太大了
                break
            
            if n % pq == 0:
                r = n // pq
                if r > 1 and isPrime(r) and isPrime(p) and isPrime(q):
                    return pp, p, q, r
            
            pp += 97
    
    return None

import time
start = time.time()

# 由于 n 是 2042 bit，p*q 可能很大
# 让我们估算 pp 的上界
# p ≈ pp², q ≈ pp², 所以 p*q ≈ pp⁴
# 如果 p*q < n (因为 n = p*q*r 且 r > 1)，则 pp⁴ < n
# pp < n^(1/4)
def integer_nth_root(n, k):
    """计算 n 的 k 次方根的整数部分"""
    if n < 0:
        return None
    if n == 0:
        return 0
    x = n
    while True:
        x1 = ((k-1)*x + n // (x**(k-1))) // k
        if x1 >= x:
            return x
        x = x1

pp_upper = integer_nth_root(n, 4) + 1
print(f"pp 的理论上界: {pp_upper} (约 {pp_upper.bit_length()} bit)")

# 这还是太大了... 需要更多约束

# 让我们尝试使用 GCD 方法
# oracle(97) 返回 ans，ans² ≡ 97 (mod n)
# 我们可以尝试 gcd(f(pp) - p, n) 对于猜测的 pp

# 但首先，让我们确认理解题意
# 也许 pp 实际上比较小？

print("\n尝试小范围搜索 pp < 10^8...")

found = False
for pp in range(1, 10**8):
    p = pp*pp + 3*pp + 3
    q = pp*pp + 5*pp + 7
    pq = p * q
    
    if pq > n:
        print(f"搜索停止: pq > n at pp = {pp}")
        break
    
    if n % pq == 0:
        r = n // pq
        if isPrime(r) and isPrime(p) and isPrime(q):
            print(f"\n找到! pp = {pp}")
            print(f"p = {p}")
            print(f"q = {q}")
            print(f"r = {r}")
            
            phi = (p-1) * (q-1) * (r-1)
            e = 65537
            d = pow(e, -1, phi)
            m = pow(c, d, n)
            flag = long_to_bytes(int(m))
            print(f"\nFlag: {flag}")
            found = True
            break
    
    if pp % 1000000 == 0:
        print(f"Progress: pp = {pp}, time = {time.time() - start:.1f}s")

if not found:
    print("小范围内未找到，可能需要更高级的方法")
    
elapsed = time.time() - start
print(f"\n总耗时: {elapsed:.1f}s")
