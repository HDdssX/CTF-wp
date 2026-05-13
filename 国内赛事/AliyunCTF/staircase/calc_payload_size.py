#!/usr/bin/env python3
"""
尝试利用已证明的注入能力来做一些有用的事情

由于空间限制，我们无法放入完整的 URLDNS payload (242+ bytes)
但我们可以尝试：
1. 注入一个简单的对象，利用其副作用
2. 或者找到一种方式来扩展可用空间

策略探索：

1. 注入 URL 对象本身（不包装在 HashMap 中）
   - URL.readObject() 不会自动触发 DNS
   - 需要 HashMap 来调用 hashCode()

2. 注入 HashMap（如果空间够）
   - 最小的 HashMap payload 还是太大...

3. 利用 Spring/其他库中的短 gadget
   - 需要研究具体的类

4. 扩展可用空间的方法：
   - 修改 MapDB 索引让它指向文件的其他位置？
   - 写入到另一个文件？

让我计算一下如果使用 TC_STRING 策略，最大可以放多少 payload：

从 0x100249 开始，到 0x1002FF 结束（不破坏索引）
可用写入空间：0x1002FF - 0x100249 = 0xB6 = 182 bytes
= 9 个 chunks (182 / 20 = 9.1)

每个 chunk 的 DATA 是 8 bytes
总 DATA = 9 * 8 = 72 bytes

使用 TC_STRING 策略后：
- Chunk 0: 7 bytes overhead (stream header + TC_STRING + length) + 1 byte payload
- 每后续 chunk 对 (2 chunks) 能放约：
  - Chunk N: 6 bytes payload + 2 bytes (TC_STRING 头)
  - Chunk N+1: 1 byte (length low) + 5 bytes payload + 2 bytes (TC_STRING 头) 或者
  - 需要更仔细的计算...

实际上，让我简化：
- 第一次 TC_STRING 吃掉 13 bytes (1+5+7)
- 之后每个 chunk 的 8 bytes 可用

那就是：
- Chunk 0: 8 bytes (stream header + TC_STRING(13) + 1 byte)
- Chunk 1: 8 bytes 可用，但末尾还有 <end><start>...
- 需要再用 TC_STRING 吃掉 12 bytes

如果 Chunk 1 DATA = [PAYLOAD 6] + [74 00]
Chunk 2 DATA = [0D XX PAYLOAD 4] + [74 00]
...

这样每 2 chunks = 6 + 4 = 10 bytes payload
有 8 个 payload chunks (chunk 1-8) = 4 对 = 40 bytes payload

加上第一个 chunk 的 1 byte (被吃掉了其实)... 还是 ~40 bytes

40 bytes 能放什么？

让我生成一个 40 bytes 以内的测试 payload...

最短的 "有用" 反序列化 payload 是什么？
"""

# 计算各种对象的序列化大小

import struct

def calc_url_size(host):
    """计算单独 URL 对象的序列化大小（不含 HashMap）"""
    size = 0
    size += 4  # stream header
    size += 2  # TC_OBJECT + TC_CLASSDESC
    size += 2 + 12  # class name length + "java.net.URL"
    size += 8  # serialVersionUID
    size += 3  # flags + field count
    
    # 7 fields
    size += 1 + 2 + 8  # I hashCode
    size += 1 + 2 + 4  # I port
    size += 1 + 2 + 9 + 1 + 2 + 18  # L authority + String type
    size += 1 + 2 + 4 + 1 + 4  # L file + ref
    size += 1 + 2 + 4 + 1 + 4  # L host + ref
    size += 1 + 2 + 8 + 1 + 4  # L protocol + ref
    size += 1 + 2 + 3 + 1 + 4  # L ref + ref
    
    size += 2  # TC_ENDBLOCKDATA + TC_NULL
    
    # Values
    size += 4 + 4  # hashCode, port
    size += 1 + 2 + len(host)  # authority string
    size += 1 + 2 + 1  # file "/"
    size += 1 + 4  # host ref
    size += 1 + 2 + 4  # protocol "http"
    size += 1  # ref null
    size += 1  # TC_ENDBLOCKDATA
    
    return size

def calc_hashmap_overhead():
    """HashMap 相对于直接序列化 key 的额外开销"""
    size = 0
    size += 2  # TC_OBJECT + TC_CLASSDESC
    size += 2 + 17  # "java.util.HashMap"
    size += 8  # serialVersionUID
    size += 3  # flags + field count
    size += 1 + 2 + 10  # F loadFactor
    size += 1 + 2 + 9   # I threshold
    size += 2  # TC_ENDBLOCKDATA + TC_NULL
    size += 4 + 4 + 4 + 4  # loadFactor, threshold, capacity, size
    size += 1  # value (TC_NULL)
    size += 1  # TC_ENDBLOCKDATA
    return size

print("URL object sizes:")
for host in ["a", "x.cn", "test.com"]:
    print(f"  URL(host='{host}'): {calc_url_size(host)} bytes")

print(f"\nHashMap overhead: {calc_hashmap_overhead()} bytes")
print(f"Total URLDNS (URL + HashMap): {calc_url_size('a') + calc_hashmap_overhead()} bytes")

# 实际测试表明最小的 URLDNS 是 ~242 bytes
print(f"\nActual minimal URLDNS: ~242 bytes")
print(f"Available space with TC_STRING strategy: ~40 bytes")
print(f"\nGap: ~200 bytes - too large!")
