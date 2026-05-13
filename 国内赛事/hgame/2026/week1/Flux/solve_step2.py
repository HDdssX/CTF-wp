
def shash_step_mod(value, key, modulus):
    # Simulate shash mod 2^k
    # Input key is the full key (but only lower bits matter for this check)
    length = len(value)
    mask = modulus - 1 # effectively we just want to keep lower bits, so we can use mask or just % modulus
    # original mask is 2**256 - 1.
    # Logic: x = (x * key) & (2**256 - 1) ^ ord(c)
    # mod modulus (where modulus <= 2**256):
    # ((x * key) & large_mask) % modulus
    # Since modulus is power of 2 and <= 2**256, (A & large_mask) % modulus == A % modulus.
    
    x = (ord(value[0]) << 7)
    # The original init: x = (ord(value[0]) << 7) & mask
    # Since we work mod modulus, and x is small, it's fine.
    
    for c in value:
        # x = (key * x) & mask ^ ord(c)
        # We model this as: term = (key * x) ; x = term ^ ord(c)
        # We need to perform this modulo modulus.
        # But XOR is bitwise.
        # Compute exact logic on lower bits:
        term = (key * x) # This multiplication valid for lower bits
        # XOR with ord(c) affects lower 8 bits.
        # We can just do bitwise operations and then take modulo.
        x = term ^ ord(c)
        # However, to prevent x growing indefinitely in our simulation, can we truncate?
        # Yes, we only care about 'modulus' bits.
        x = x & (modulus - 1)
        
    x ^= length
    return x & (modulus - 1)

def solve_key():
    h_candidates = [
        6866312363291178484982959720124435011938375586579989365225276248801007329194,
        1851471554044636937620060405470139203302636010497407478542185697214766136647
    ]
    value = "Welcome to HGAME 2026!"
    
    for idx, h_target in enumerate(h_candidates):
        print(f"Checking candidate h{idx+1}: {h_target}")
        
        possible_keys = [0] # Start with 0 bits determined
        
        for bit in range(70):
            modulus = 1 << (bit + 1)
            target_mod = h_target & (modulus - 1)
            
            next_keys = []
            for k_base in possible_keys:
                for bit_val in [0, 1]:
                    k_test = k_base | (bit_val << bit)
                    
                    res = shash_step_mod(value, k_test, modulus)
                    
                    if res == target_mod:
                        next_keys.append(k_test)
            
            possible_keys = next_keys
            # print(f"Bit {bit}: {len(possible_keys)} candidates")
            if not possible_keys:
                break
        
        if possible_keys:
            print(f"Found Key Candidates for h{idx+1}: {possible_keys}")
            for k in possible_keys:
                # Output Flag
                # flag = "VIDAR{" + hex(shash(magic_word, key))[2:] + "}"
                # But I need to reimplement full shash first
                print(f"KEY: {k}")

def full_shash_solve(key):
    def shash(value, key):
        length = len(value)
        if length == 0: return 0
        mask = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
        x = (ord(value[0]) << 7) & mask
        for c in value:
            x = (key * x) & mask ^ ord(c)
        x ^= length & mask
        return x

    magic_word = "I get the key now!"
    flag_hash = shash(magic_word, key)
    flag = "VIDAR{" + hex(flag_hash)[2:] + "}"
    print(flag)

solve_key()
