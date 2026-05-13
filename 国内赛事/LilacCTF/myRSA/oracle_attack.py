"""
利用 Oracle 分解 n

Oracle 功能: 给定 x (80 < x < 100, 非完全平方)，返回 x 的模 n 平方根（如果存在）

关键洞察:
1. 如果 oracle 返回 ans，则 ans² ≡ x (mod n)
2. 由于 n = p*q*r，对于同一个 x，有多个平方根
3. 如果我们找到两个不同的平方根 a 和 b，满足 a² ≡ b² (mod n)
   则 gcd(a-b, n) 或 gcd(a+b, n) 可能给出 n 的因子

但更重要的是:
- oracle 内部用 CRT 组合 sqrt_mod(x, p), sqrt_mod(x, q), sqrt_mod(x, r)
- 如果任一返回 None (x 不是二次剩余)，则返回 🤐

所以通过测试哪些 x 返回值，哪些返回 🤐，可以获得关于 p, q, r 模小数的信息！
"""

import socket
from math import gcd
from Crypto.Util.number import long_to_bytes, isPrime

def connect_and_get_data():
    """连接服务器获取 n, c 和 oracle 响应"""
    s = socket.socket()
    s.settimeout(30)
    s.connect(('101.245.90.119', 8089))
    
    # 接收 n 和 c
    data = b''
    while b'>' not in data:
        data += s.recv(4096)
    
    text = data.decode()
    print("Received:", text[:500])
    
    # 解析 n 和 c
    lines = text.strip().split('\n')
    n_line = [l for l in lines if l.startswith('n = ')][0]
    c_line = [l for l in lines if l.startswith('c = ')][0]
    
    n = int(n_line.split('=')[1].strip())
    c = int(c_line.split('=')[1].strip())
    
    print(f"\nn = {n}")
    print(f"c = {c}")
    
    # 测试所有可用的 oracle 输入
    # 80 < x < 100, 非完全平方 (排除 81=9², 100=10², 但100不在范围内)
    test_values = [82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99]
    
    oracle_results = {}
    
    for x in test_values:
        s.send(f"{x}\n".encode())
        response = s.recv(4096).decode().strip()
        
        # 检查是否是数字或 🤐
        lines = response.split('\n')
        result_line = lines[0] if lines else response
        
        if '🤐' in result_line:
            oracle_results[x] = None
            print(f"oracle({x}) = 🤐")
        else:
            try:
                # 尝试提取数字
                ans = int(result_line.replace('🧭 >', '').strip())
                oracle_results[x] = ans
                print(f"oracle({x}) = {ans}")
            except:
                # 可能格式问题，打印原始响应
                print(f"oracle({x}) raw response: {repr(result_line)}")
                oracle_results[x] = None
    
    s.close()
    return n, c, oracle_results


def analyze_oracle_results(n, oracle_results):
    """分析 oracle 结果来分解 n"""
    
    print("\n" + "="*60)
    print("分析 Oracle 结果")
    print("="*60)
    
    # 对于返回数值的 x，尝试 gcd 分解
    for x, ans in oracle_results.items():
        if ans is not None:
            # ans² ≡ x (mod n)
            # gcd(ans, n) 可能揭示因子
            g = gcd(ans, n)
            if 1 < g < n:
                print(f"[!] gcd(oracle({x}), n) = {g} - 这是一个因子！")
                return g
            
            # 另一种方法：如果 x 有整数平方根（如 x=84=4*21, x=96=16*6），
            # 我们知道另一个平方根
            # ...
    
    # 利用二次剩余的性质
    # 如果 oracle(x) = 🤐，说明 x 不是 p, q, r 中至少一个的二次剩余
    
    # 对于小素数 x，我们可以用二次互反律
    # Legendre(x, p) = 1 当且仅当 x^((p-1)/2) ≡ 1 (mod p)
    # 由二次互反律: Legendre(x, p) = Legendre(p, x) * (-1)^(...) 当 x 是奇素数
    
    # 可用素数: 83, 89, 97
    primes_in_range = [83, 89, 97]
    
    print("\n分析二次剩余模式...")
    for x in primes_in_range:
        if x in oracle_results:
            status = "✓ 二次剩余" if oracle_results[x] is not None else "✗ 非二次剩余"
            print(f"  {x}: {status}")
    
    return None


def factor_using_multiple_roots(n, x, ans):
    """
    给定 oracle(x) = ans (ans² ≡ x mod n)，尝试找另一个平方根来分解
    
    由于 n = p*q*r，x 有 8 个平方根（如果对所有因子都是QR）
    它们是 ±a, ±b, ±c, ... 的 CRT 组合
    
    oracle 返回其中一个，我们需要找另一个
    """
    
    # 简单尝试：n - ans 是另一个平方根
    other = n - ans
    # gcd(ans - other, n) = gcd(2*ans, n)
    g = gcd(2 * ans, n)
    if 1 < g < n:
        return g
    
    # 更复杂：如果我们有两个不同的 x 的平方根结果...
    # 但 oracle 对同一个 x 总是返回同一个结果（确定性的）
    
    return None


def decrypt(n, c, factors):
    """使用因子解密"""
    p, q, r = factors
    phi = (p - 1) * (q - 1) * (r - 1)
    e = 65537
    d = pow(e, -1, phi)
    m = pow(c, d, n)
    flag = long_to_bytes(int(m))
    return flag


if __name__ == "__main__":
    print("="*60)
    print("myRSA Challenge - Oracle Attack")
    print("="*60)
    
    try:
        n, c, oracle_results = connect_and_get_data()
        
        # 分析 oracle 结果
        factor = analyze_oracle_results(n, oracle_results)
        
        if factor:
            print(f"\n成功分解! 找到因子: {factor}")
            # 继续分解...
        else:
            print("\n直接 gcd 方法未能分解")
            print("需要进一步分析...")
            
            # 保存数据供后续分析
            print(f"\nn = {n}")
            print(f"c = {c}")
            print(f"oracle_results = {oracle_results}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
