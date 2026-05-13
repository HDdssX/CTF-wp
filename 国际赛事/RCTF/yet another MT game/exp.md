原因与修复一步到位：

**为什么会报错**

- 你在做 `d = pow(e, -1, P - 1)`，但这里 `gcd(e, P-1) ≠ 1`，具体是
   `gcd(1074888996, 2^19937-20023-1) = 12`，所以 `e` 在模 `P-1` 下**不可逆**，`pow(e,-1, P-1)` 直接抛 `ValueError`。([Docs.rs](https://docs.rs/crate/gmp-mpfr-sys/1.4.11/source/gmp-6.2.1-c/rand/randmts.c))

**正确做法**

- 记 (P = 2^{19937}-20023)，(e=1074888996)，(g=\gcd(e,P-1)=12)。
- 把 (e) 因子 12 抽掉：(e' = e/12 = 89574083)。此时 (\gcd(e',P-1)=1)，所以 **(e')** 在模 (P-1) 下可逆。
- 令 (d = (e')^{-1} \bmod (P-1))，然后
   [
   x^{12} \equiv (x^{e})^{d} \equiv \text{seed2}^{,d} \pmod P .
   ]
   这里 (x=\text{seed1}=\text{secret}+2)。
- 由于 `secret` 只有 512 位，((\text{secret}+2)^{12} < 2^{6144} \ll P)，所以上式**没有发生模回绕**，即
   [
   \text{seed1}^{12} = \text{seed2}^{,d}\quad(\text{整数恒等})
   ]
   直接对右边做**整数 12 次方根**即可拿到 `seed1`，再减 2 得到 `secret`。([Docs.rs](https://docs.rs/crate/gmp-mpfr-sys/1.4.11/source/gmp-6.2.1-c/rand/randmts.c))

------

## 代码改动（把你原来求逆和求 seed1 的几行替换掉）

```python
# 常量
P = (1 << 19937) - 20023
e = 1074888996

# 1) 计算 d = (e/12)^(-1) mod (P-1)
import math
g = math.gcd(e, P - 1)          # = 12
assert g == 12
e_prime = e // g                 # 89574083
d = pow(e_prime, -1, P - 1)      # 这里一定可逆

# 2) 先把 seed2 提前算好（你已从 mt[] 拼出来的那个 19937 位大整数）
# seed2 = ... (略)

# 3) 得到 seed1^12（注意这是按模 P 算，但实际上等于整数）
seed1_pow12 = pow(seed2, d, P)

# 4) 整数 12 次方根（精确根）
def iroot_exact(n, k):
    # Newton 法，返回整数根并校验是完美 k 次幂
    if n == 0:
        return 0
    # 初始近似：2^ceil(bitlen/k)
    x = 1 << ((n.bit_length() + k - 1) // k)
    while True:
        x_next = ((k - 1) * x + n // pow(x, k - 1)) // k
        if x_next >= x:
            break
        x = x_next
    # 校验
    if pow(x, k) != n:
        raise ValueError("n is not a perfect k-th power")
    return x

seed1 = iroot_exact(seed1_pow12, 12)   # 得到 seed1 = secret + 2
secret_int = seed1 - 2
secret_hex = secret_int.to_bytes(64, "big").hex()
```

这样改后：

- 不再对 (e) 直接取模逆（会报错），而是对 **(e' = e/12)** 取模逆；
- `seed1_pow12` 一定是**完美的 12 次幂**（因为来源合法），`iroot_exact` 会一次到位还原；
- `secret_int` 一定在 (0 \le \text{secret} < 2^{512})；转成 64 字节大端再 `.hex()` 回填即可。

------

## 参考依据

- GMP 的 `randmts.c` 明确：播种先做 `seed1 = seed mod (2^19937-20027) + 2`，再做 `seed2 = seed1^1074888996 (mod 2^19937-20023)`，然后把 19937 位拆装进 `mt[]` 并 `WARM_UP`。常量与流程见源码注释与实现。([Docs.rs](https://docs.rs/crate/gmp-mpfr-sys/1.4.11/source/gmp-6.2.1-c/rand/randmts.c))

如果你已经从 `mt[]` 拼回了 `seed2`，把上述补丁塞进去即可消除报错并正确还原 `secret`。