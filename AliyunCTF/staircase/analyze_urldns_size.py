#!/usr/bin/env python3
"""
分析 URLDNS payload 的各部分大小
"""
import struct

def analyze_urldns_size(host):
    """分析 URLDNS payload 各部分大小"""
    
    parts = []
    
    # Stream header
    parts.append(("Stream header", 4))
    
    # HashMap object header
    parts.append(("HashMap: TC_OBJECT + TC_CLASSDESC", 2))
    parts.append(("HashMap: class name length", 2))
    parts.append(("HashMap: 'java.util.HashMap'", 17))
    parts.append(("HashMap: serialVersionUID", 8))
    parts.append(("HashMap: flags + field count", 3))
    
    # HashMap fields
    parts.append(("HashMap: F loadFactor", 1 + 2 + 10))  # typecode + len + name
    parts.append(("HashMap: I threshold", 1 + 2 + 9))
    
    # HashMap end + superclass
    parts.append(("HashMap: TC_ENDBLOCKDATA + TC_NULL", 2))
    
    # HashMap data
    parts.append(("HashMap: loadFactor value", 4))
    parts.append(("HashMap: threshold value", 4))
    parts.append(("HashMap: capacity", 4))
    parts.append(("HashMap: size", 4))
    
    # URL object
    parts.append(("URL: TC_OBJECT + TC_CLASSDESC", 2))
    parts.append(("URL: class name length", 2))
    parts.append(("URL: 'java.net.URL'", 12))
    parts.append(("URL: serialVersionUID", 8))
    parts.append(("URL: flags + field count", 3))
    
    # URL fields (7 fields)
    parts.append(("URL: I hashCode", 1 + 2 + 8))
    parts.append(("URL: I port", 1 + 2 + 4))
    
    # String type descriptor (defined once, referenced later)
    parts.append(("URL: L authority + TC_STRING", 1 + 2 + 9 + 1 + 2 + 18))  # L + len + "authority" + TC_STRING + len + "Ljava/lang/String;"
    
    # References to String type
    parts.append(("URL: L file + TC_REFERENCE", 1 + 2 + 4 + 1 + 4))
    parts.append(("URL: L host + TC_REFERENCE", 1 + 2 + 4 + 1 + 4))
    parts.append(("URL: L protocol + TC_REFERENCE", 1 + 2 + 8 + 1 + 4))
    parts.append(("URL: L ref + TC_REFERENCE", 1 + 2 + 3 + 1 + 4))
    
    # URL end
    parts.append(("URL: TC_ENDBLOCKDATA + TC_NULL", 2))
    
    # URL data
    parts.append(("URL: hashCode value", 4))
    parts.append(("URL: port value", 4))
    
    # String values
    host_len = len(host)
    parts.append((f"URL: authority string (TC_STRING + len + '{host}')", 1 + 2 + host_len))
    parts.append(("URL: file string '/'", 1 + 2 + 1))
    parts.append(("URL: host TC_REFERENCE", 1 + 4))
    parts.append(("URL: protocol string 'http'", 1 + 2 + 4))
    parts.append(("URL: ref TC_NULL", 1))
    
    # URL end data
    parts.append(("URL: TC_ENDBLOCKDATA", 1))
    
    # HashMap entry value (null)
    parts.append(("HashMap: value TC_NULL", 1))
    
    # HashMap end
    parts.append(("HashMap: TC_ENDBLOCKDATA", 1))
    
    # Print analysis
    total = 0
    print(f"URLDNS payload analysis (host='{host}', {host_len} chars):")
    print("-" * 60)
    for name, size in parts:
        total += size
        print(f"  {name}: {size} bytes (累计: {total})")
    print("-" * 60)
    print(f"Total: {total} bytes")
    
    return total

# 测试不同长度的域名
for host in ["a", "x.cn", "ab.cn", "dnslog.cn", "abcdefgh.dnslog.cn"]:
    size = analyze_urldns_size(host)
    print(f"\nWith host='{host}': {size} bytes")
    print()
