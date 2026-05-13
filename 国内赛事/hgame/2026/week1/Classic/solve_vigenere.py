
def decrypt_vigenere(ciphertext, key):
    key_indices = [ord(k.lower()) - 97 for k in key]
    key_len = len(key)
    plaintext = []
    key_idx = 0
    
    for char in ciphertext:
        if 'a' <= char.lower() <= 'z':
            is_upper = char.isupper()
            c_val = ord(char.lower()) - 97
            k_val = key_indices[key_idx % key_len]
            
            # Decrypt: P = (C - K) % 26
            p_val = (c_val - k_val) % 26
            p_char = chr(p_val + 97)
            
            if is_upper:
                p_char = p_char.upper()
            
            plaintext.append(p_char)
            key_idx += 1
        else:
            plaintext.append(char)
            
    return "".join(plaintext)

with open('task/flag.txt', 'r', encoding='utf-8') as f:
    text = f.read()

key = "HGAME"
decrypted = decrypt_vigenere(text, key)
print(decrypted)
