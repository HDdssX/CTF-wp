"""
完整逆向 "There_is_nothing_you_wanna_get.." 字符串的过程
"""
import struct

# 读取ROM
with open("rom.bin", "rb") as f:
    data = f.read()

print("=" * 60)
print("Step 1: 定位验证函数 (0x4AB0)")
print("=" * 60)
print("""
在字节码解释器 (0x4D00) 中，当遇到 0xEE 操作码时会调用 0x4AB0:
    0x4ef4: call 0x4ab0    ; 调用验证函数
""")

print("\n" + "=" * 60)
print("Step 2: 分析 0x4AB0 处的 SPARC 指令")
print("=" * 60)

# 反汇编 0x4AB0 - 0x4B80 区域
def decode_sethi_or(data, offset):
    """解码 sethi + or 指令对，提取32位立即数"""
    instr1 = struct.unpack('>I', data[offset:offset+4])[0]
    instr2 = struct.unpack('>I', data[offset+4:offset+8])[0]
    
    # sethi: imm22 在低22位
    imm22 = instr1 & 0x3FFFFF
    hi = imm22 << 10  # sethi 将 imm22 放到高22位
    
    # or: simm13 在低13位
    simm13 = instr2 & 0x1FFF
    if simm13 & 0x1000:  # 符号扩展
        simm13 -= 0x2000
    
    value = (hi | (simm13 & 0x3FF)) & 0xFFFFFFFF
    return value

print("""
在 0x4AB0 函数中发现了大量 sethi + or 指令对：
每对指令构造一个 32 位值，每个值包含 4 个 ASCII 字符。
""")

# 提取所有 sethi+or 对的偏移量（从反汇编结果中获得）
# 这些是构造字符串的指令位置
string_construction_offsets = [
    0x4AB4,  # "Ther"
    0x4ABC,  # "e_is"
    0x4AC8,  # "_not"
    0x4AD0,  # "hing"
    0x4ADC,  # "_you"
    0x4AE4,  # "_wan"
    0x4AF0,  # "na_g"
    0x4AF8,  # "et.."
]

print("从 SPARC 指令中提取的 sethi+or 指令对:")
print("-" * 60)

reconstructed_string = b""

for i, offset in enumerate(string_construction_offsets):
    # 读取 sethi 指令
    sethi_instr = struct.unpack('>I', data[offset:offset+4])[0]
    # 读取 or 指令
    or_instr = struct.unpack('>I', data[offset+4:offset+8])[0]
    
    # 解码 sethi: op=00, rd, op2=100, imm22
    imm22 = sethi_instr & 0x3FFFFF
    rd_sethi = (sethi_instr >> 25) & 0x1F
    
    # 解码 or: op=10, rd, op3=000010, rs1, i=1, simm13
    simm13 = or_instr & 0x1FFF
    rd_or = (or_instr >> 25) & 0x1F
    
    # 构造完整的32位值
    # sethi 将 imm22 放到 bits[31:10]
    # or 将 simm13 的低10位放到 bits[9:0]
    hi_part = imm22 << 10
    lo_part = simm13 & 0x3FF
    full_value = hi_part | lo_part
    
    # 转换为字节（大端序，因为是 SPARC）
    value_bytes = struct.pack('>I', full_value)
    
    print(f"  Offset 0x{offset:04X}:")
    print(f"    sethi 0x{imm22:06x}, %r{rd_sethi}   ; 指令: 0x{sethi_instr:08x}")
    print(f"    or    %r{rd_or}, 0x{simm13:03x}, %r{rd_or}   ; 指令: 0x{or_instr:08x}")
    print(f"    => 构造值: 0x{full_value:08X} = \"{value_bytes.decode('latin-1')}\"")
    print()
    
    reconstructed_string += value_bytes

print("=" * 60)
print("Step 3: 重建完整字符串")
print("=" * 60)
print(f"\n拼接所有 4 字节块:")
print(f"  {reconstructed_string}")
print(f"\n最终字符串: \"{reconstructed_string.decode('latin-1')}\"")

print("\n" + "=" * 60)
print("Step 4: 验证 - 直接从原始指令计算")
print("=" * 60)

# 直接从ROM中读取并解析每条指令
raw_instructions = []
for offset in range(0x4AB4, 0x4B00, 4):
    instr = struct.unpack('>I', data[offset:offset+4])[0]
    raw_instructions.append((offset, instr))

print("\n原始指令序列 (0x4AB4 - 0x4B00):")
for offset, instr in raw_instructions[:16]:
    op = (instr >> 30) & 0x3
    if op == 0:  # sethi
        op2 = (instr >> 22) & 0x7
        if op2 == 4:
            imm22 = instr & 0x3FFFFF
            rd = (instr >> 25) & 0x1F
            print(f"  0x{offset:04X}: sethi 0x{imm22:06x}, %r{rd}")
    elif op == 2:  # or
        op3 = (instr >> 19) & 0x3F
        if op3 == 2:  # or
            rd = (instr >> 25) & 0x1F
            simm13 = instr & 0x1FFF
            print(f"  0x{offset:04X}: or %r{rd}, 0x{simm13:03x}, %r{rd}")

print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print("""
SPARC 使用 sethi + or 指令对来加载 32 位立即数：

1. sethi imm22, %rd  
   - 将 22 位立即数左移 10 位后存入寄存器
   - %rd = imm22 << 10

2. or %rd, simm13, %rd
   - 将寄存器与 13 位立即数进行或运算
   - %rd = %rd | (simm13 & 0x3FF)

组合效果: %rd = (imm22 << 10) | (simm13 & 0x3FF) = 完整的 32 位值

每个 32 位值包含 4 个 ASCII 字符（大端序）。
8 对指令 × 4 字节 = 32 字节字符串。
""")

print(f"最终结果: {reconstructed_string.decode('latin-1')}")
