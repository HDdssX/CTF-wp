#!/usr/bin/env python3
"""
分析 HashSet 版本的 URLDNS payload 大小
HashSet 在反序列化时也会调用元素的 hashCode()
"""
import struct

def analyze_hashset_urldns_size(host):
    """使用 HashSet 代替 HashMap"""
    
    parts = []
    
    # Stream header
    parts.append(("Stream header", 4))
    
    # HashSet 实际上底层用的是 HashMap，所以可能更大...
    # 让我检查 HashSet 的序列化格式
    
    # HashSet object header
    parts.append(("HashSet: TC_OBJECT + TC_CLASSDESC", 2))
    parts.append(("HashSet: class name length", 2))
    parts.append(("HashSet: 'java.util.HashSet'", 17))
    parts.append(("HashSet: serialVersionUID", 8))
    parts.append(("HashSet: flags", 1))
    parts.append(("HashSet: field count (0)", 2))
    
    # HashSet 没有字段，但 writeObject 会写入额外数据
    
    # TC_ENDBLOCKDATA + TC_NULL
    parts.append(("HashSet: TC_ENDBLOCKDATA + TC_NULL", 2))
    
    # HashSet writeObject 数据:
    # - capacity (int)
    # - loadFactor (float)  
    # - size (int)
    # - elements
    parts.append(("HashSet: capacity", 4))
    parts.append(("HashSet: loadFactor", 4))
    parts.append(("HashSet: size", 4))
    
    # URL 对象 (和之前一样)
    parts.append(("URL: TC_OBJECT + TC_CLASSDESC", 2))
    parts.append(("URL: class name length", 2))
    parts.append(("URL: 'java.net.URL'", 12))
    parts.append(("URL: serialVersionUID", 8))
    parts.append(("URL: flags + field count", 3))
    
    parts.append(("URL: I hashCode", 1 + 2 + 8))
    parts.append(("URL: I port", 1 + 2 + 4))
    
    parts.append(("URL: L authority + TC_STRING", 1 + 2 + 9 + 1 + 2 + 18))
    parts.append(("URL: L file + TC_REFERENCE", 1 + 2 + 4 + 1 + 4))
    parts.append(("URL: L host + TC_REFERENCE", 1 + 2 + 4 + 1 + 4))
    parts.append(("URL: L protocol + TC_REFERENCE", 1 + 2 + 8 + 1 + 4))
    parts.append(("URL: L ref + TC_REFERENCE", 1 + 2 + 3 + 1 + 4))
    
    parts.append(("URL: TC_ENDBLOCKDATA + TC_NULL", 2))
    
    parts.append(("URL: hashCode value", 4))
    parts.append(("URL: port value", 4))
    
    host_len = len(host)
    parts.append((f"URL: authority string", 1 + 2 + host_len))
    parts.append(("URL: file string '/'", 1 + 2 + 1))
    parts.append(("URL: host TC_REFERENCE", 1 + 4))
    parts.append(("URL: protocol string 'http'", 1 + 2 + 4))
    parts.append(("URL: ref TC_NULL", 1))
    
    parts.append(("URL: TC_ENDBLOCKDATA", 1))
    
    # HashSet 结束
    parts.append(("HashSet: TC_ENDBLOCKDATA", 1))
    
    total = sum(size for _, size in parts)
    
    print(f"HashSet URLDNS (host='{host}'): {total} bytes")
    
    return total

# 计算 HashMap 的 overhead
def calc_hashmap_overhead():
    """HashMap 相比 HashSet 多出的部分"""
    # HashMap 需要:
    # - 两个字段定义 (loadFactor, threshold)
    # - 字段值
    # - value (null)
    
    overhead = (13 + 12 +  # field definitions
                4 + 4 +     # field values
                4 + 4 +     # capacity, size in writeObject
                1)          # value null
    print(f"HashMap overhead: ~{overhead} bytes")

analyze_hashset_urldns_size("a")
analyze_hashset_urldns_size("x.cn")
calc_hashmap_overhead()

# 实际上 HashSet 和 HashMap 差不多
# 让我想想其他方法...
print("\n让我考虑直接的 URL 对象...")
# 直接序列化 URL 对象，然后用其他方式触发 hashCode()?
