"""
重新获取并验证 oracle 数据
"""
import socket

def get_oracle_data():
    s = socket.socket()
    s.settimeout(30)
    s.connect(('101.245.90.119', 8089))
    
    # 接收 n 和 c
    data = b''
    while b'>' not in data:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
    
    text = data.decode()
    
    # 解析 n 和 c
    import re
    n_match = re.search(r'n = (\d+)', text)
    c_match = re.search(r'c = (\d+)', text)
    
    n = int(n_match.group(1))
    c = int(c_match.group(1))
    
    print(f"n = {n}")
    print(f"c = {c}")
    print(f"n bits = {n.bit_length()}")
    
    # 只测试 97
    s.send(b"97\n")
    
    # 接收响应
    response = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        response += chunk
        if b'>' in response:
            break
    
    resp_text = response.decode()
    print(f"\nRaw response for 97: {repr(resp_text)}")
    
    # 提取数字
    lines = resp_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('🧭'):
            try:
                ans = int(line)
                print(f"\noracle(97) = {ans}")
                print(f"ans bits = {ans.bit_length()}")
                
                # 验证
                check = pow(ans, 2, n)
                print(f"ans² mod n = {check}")
                print(f"ans² mod n == 97? {check == 97}")
                
                return n, c, ans
            except:
                pass
    
    s.close()
    return n, c, None

if __name__ == "__main__":
    n, c, ans = get_oracle_data()
