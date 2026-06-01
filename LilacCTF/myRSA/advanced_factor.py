"""
核心攻击思路:

oracle(97) 返回 ans，满足 ans² ≡ 97 (mod n)
由于 n = p*q*r，ans 是通过 CRT 组合 sqrt(97) mod p, q, r 得到的

关键观察：
设 sp = sqrt(97) mod p (oracle 选择的那个根)
设 sq = sqrt(97) mod q
设 sr = sqrt(97) mod r

则 ans = CRT(sp, sq, sr)

由于 p = pp² + 3pp + 3, q = pp² + 5pp + 7
sp 和 sq 都与 pp 相关！

如果我们能找到 sp 和 sq 与 pp 的关系，就可以利用 ans 来求解 pp

更精确地：
sp² ≡ 97 (mod p)
sq² ≡ 97 (mod q)

设 sp = a*pp + b (mod p) 对于某些 a, b
这就把 sp 与 pp 联系起来了

实际上，更直接的利用方式：
CRT 的逆过程：
ans ≡ sp (mod p)
ans ≡ sq (mod q)
ans ≡ sr (mod r)

所以 sp = ans mod p
但我们不知道 p...

换一种思路：
gcd(ans² - 97, n) = n (因为 ans² ≡ 97 mod n)
但 gcd((ans - x)² - 97, n) 对于某个特殊的 x 可能给出因子

最直接的方法：利用 CRT 的线性组合性质
ans = sp * (qr) * inv(qr, p) + sq * (pr) * inv(pr, q) + sr * (pq) * inv(pq, r) (mod n)
其中 qr = q*r, pr = p*r, pq = p*q

这太复杂了...

让我们回到基础：
问题是 pp 可能很大 (约 256 bit)

但题目说 "pick up your Sagemath"，暗示需要代数方法

方法：多项式 resultant / GCD
在模 p 下：x² + 3x + 3 = p 有根 pp
在模 q 下：x² + 5x + 7 = q 有根 pp

设 f(x) = x² + 3x + 3
设 g(x) = x² + 5x + 7
则 f(pp) = p, g(pp) = q

考虑 f(x) 和 g(x) 在模 n 下的性质：
f(pp) * g(pp) = p * q
n / r = p * q
所以 (f(pp) * g(pp)) | n

设 h(x) = f(x) * g(x) = (x² + 3x + 3)(x² + 5x + 7)
            = x⁴ + 8x³ + 25x² + 36x + 21

h(pp) = p * q = n / r

如果我们知道 h(x) 在模 n 下的某个性质...

啊！关键点：
gcd(h(x) - n/r, n) 当 x = pp 时应该是 n
但我们不知道 r...

另一个想法：
n ≡ 0 (mod p)
n ≡ 0 (mod q)
所以 n mod f(pp) = 0, n mod g(pp) = 0

在模 n 下：
gcd(n, f(x)) 当 x 遍历时，如果 x = pp，则 gcd = p (因为 f(pp) = p | n)

所以我们可以计算 gcd(f(x), n) 对于不同的 x，找到 x = pp 时给出因子 p

但 pp 太大，不能直接遍历...

等等！oracle 给了我们额外信息！
ans² ≡ 97 (mod p)
这等价于 ans mod p 是 sqrt(97) mod p

设 s97p = sqrt(97) mod p (选择 oracle 用的那个根)
则 ans ≡ s97p (mod p)

同样 ans ≡ s97q (mod q), ans ≡ s97r (mod r)

关键：s97p 是 p 的函数，而 p = pp² + 3pp + 3 是 pp 的函数
所以 s97p 是 pp 的（复杂的）函数

使用 Tonelli-Shanks 算法，sqrt(97) mod p 可以写成关于 p 的表达式

Tonelli-Shanks 的关键：设 p - 1 = 2^s * t
sqrt(97) = 97^((t+1)/2) * (factor)^k mod p
其中 factor 是一个二次非剩余，k 是某个调整值

这依赖于 p 的结构...

更简单的方法：利用 97 是小数
对于 p 这样的大素数，sqrt(97) mod p 的计算涉及 97^((p+1)/4) 当 p ≡ 3 (mod 4)
或者更复杂的表达式当 p ≡ 1 (mod 4)

检查：p = pp² + 3pp + 3
p mod 4 = (pp² + 3pp + 3) mod 4

如果 pp 是偶数：pp² ≡ 0, 3pp ≡ 0 (mod 4), 所以 p ≡ 3 (mod 4)
如果 pp ≡ 1 (mod 4): pp² ≡ 1, 3pp ≡ 3 (mod 4), 所以 p ≡ 1 + 3 + 3 = 7 ≡ 3 (mod 4)
如果 pp ≡ 2 (mod 4): pp² ≡ 0, 3pp ≡ 2 (mod 4), 所以 p ≡ 0 + 2 + 3 = 5 ≡ 1 (mod 4)
如果 pp ≡ 3 (mod 4): pp² ≡ 1, 3pp ≡ 1 (mod 4), 所以 p ≡ 1 + 1 + 3 = 5 ≡ 1 (mod 4)

所以当 pp ≡ 0, 1 (mod 4) 时，p ≡ 3 (mod 4)
当 pp ≡ 2, 3 (mod 4) 时，p ≡ 1 (mod 4)

当 p ≡ 3 (mod 4) 时，sqrt(97) = ±97^((p+1)/4) mod p

所以如果 pp ≡ 0 或 1 (mod 4):
sqrt(97) = ±97^((p+1)/4) = ±97^((pp² + 3pp + 4)/4) mod p

嗯，这还是很复杂...

让我尝试另一种方法：利用二次剩余的乘法性质
"""

from math import gcd
from Crypto.Util.number import long_to_bytes, isPrime

n = 320463398964822335046388577512598439169912412662663009494347432623554394203670803089065987779128504277420596228400774827331351610218400792101575854579340551173392220602541203502751384517150046009415263351743602382113258267162420601780488075168957353780597674878144369327869964465070900596283281886408183175554478081038993938477659926361457163384937565266894839330377063520304463379213493662243218514993889537829099698656597997161855278297938355255410088350528543369288722795261835727770017939399082258134647208444374973242138569356754462210049877096486232693547694891534331539434254781094641373606991238019101335437

c = 80140760654462267017719473677495407945806989083076205994692983838456863987736401342704400427420046369099889997909749061368480651101102957366243793278412775082041015336890704820532767466703387606369163429880159007880606865852075573350086563934479736264492605192640115037085361523151744341819385022516548746015224651520456608321954049996777342018093920514055242719341522462068436565236490888149658105227332969276825894486219704822623333003530407496629970767624179771340249861283624439879882322915841180645525481839850978628245753026288794265196088121281665948230166544293876326256961232824906231788653397049122767633

print("尝试 factordb...")
print(f"http://www.factordb.com/index.php?query={n}")

# 也可以检查 n 是否有特殊形式
print(f"\nn 的最后几位: {n % 10**10}")

# 检查 n 是否能被一些特殊数整除
print("\n检查小因子...")
small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113]
for sp in small_primes:
    if n % sp == 0:
        print(f"n 能被 {sp} 整除!")

# 检查 n 是否是完全幂
print("\n检查完全幂...")
for k in range(2, 20):
    def integer_nth_root(n, k):
        if n < 0: return None
        if n == 0: return 0
        x = n
        while True:
            x1 = ((k-1)*x + n // (x**(k-1))) // k
            if x1 >= x: return x
            x = x1
    
    root = integer_nth_root(n, k)
    if root**k == n:
        print(f"n = {root}^{k}")
        break

print("\n" + "="*60)
print("最后尝试: 利用模运算加速搜索")
print("="*60)

# 使用更多的模约束
# 已知: pp mod 97 ∈ valid_values
# 加上: pp mod 83, pp mod 89 的约束

# 对于模 m，计算使得 p*q | n (mod m) 的 pp mod m 值
# 即 (pp² + 3pp + 3)(pp² + 5pp + 7) | (n mod m^k) 对于某个 k

# 这需要更仔细的分析...

# 简化: 假设 r 是一个"普通"大小的素数，而 p, q 通过 pp 关联
# 尝试 Pollard p-1

def pollard_pm1(n, B1=10**6):
    """Pollard p-1 分解"""
    import random
    a = 2
    for p in range(2, B1):
        if isPrime(p):
            pk = p
            while pk < B1:
                a = pow(a, p, n)
                pk *= p
    g = gcd(a - 1, n)
    if 1 < g < n:
        return g
    return None

print("尝试 Pollard p-1...")
factor = pollard_pm1(n, B1=10**6)
if factor:
    print(f"找到因子: {factor}")
else:
    print("Pollard p-1 失败")

# 尝试 Pollard rho (with more iterations)
def pollard_rho_brent(n, max_iter=10**8):
    """Brent's improvement of Pollard rho"""
    import random
    if n % 2 == 0:
        return 2
    
    y, c, m = random.randint(1, n-1), random.randint(1, n-1), random.randint(1, n-1)
    g, r, q = 1, 1, 1
    
    count = 0
    while g == 1 and count < max_iter:
        x = y
        for _ in range(r):
            y = (y * y + c) % n
        
        k = 0
        while k < r and g == 1:
            ys = y
            for _ in range(min(m, r - k)):
                y = (y * y + c) % n
                q = q * abs(x - y) % n
            g = gcd(q, n)
            k += m
        r *= 2
        count += r
        
        if count % 10**6 == 0:
            print(f"  Rho progress: {count} iterations")
    
    if g == n:
        while True:
            ys = (ys * ys + c) % n
            g = gcd(abs(x - ys), n)
            if g > 1:
                break
    
    if g != n:
        return g
    return None

print("\n尝试 Pollard rho (Brent's)...")
factor = pollard_rho_brent(n, max_iter=10**7)
if factor:
    print(f"找到因子: {factor}")
    
    # 验证并分解
    if isPrime(factor):
        remaining = n // factor
        print(f"remaining = n / {factor}")
        
        # 检查 remaining 是否可以进一步分解
        if isPrime(remaining):
            print(f"remaining 是素数")
        else:
            print(f"remaining 不是素数，需要进一步分解")
else:
    print("Pollard rho 失败")
